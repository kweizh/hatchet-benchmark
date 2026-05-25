import os
import re

LOG_PATH = "/tmp/runs.log"
SLEEP_DURATION_SECONDS = 2.0
# Allow small jitter on the "intervals must not overlap" check to absorb
# filesystem flush/scheduling noise.
NON_OVERLAP_TOLERANCE_S = 0.05

LINE_RE = re.compile(
    r"^\s*(start|end)\s+(A|B)\s+([0-9]+(?:\.[0-9]+)?)\s*$"
)


def _parse_log():
    assert os.path.isfile(LOG_PATH), (
        f"{LOG_PATH} does not exist; the runner did not produce the expected "
        f"log file."
    )
    with open(LOG_PATH, "r") as fh:
        raw_lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    parsed = []
    for idx, line in enumerate(raw_lines):
        m = LINE_RE.match(line)
        assert m is not None, (
            f"Line {idx + 1} of {LOG_PATH} does not match the expected format "
            f"'<event> <user_id> <timestamp>': {line!r}"
        )
        event, user_id, ts_str = m.group(1), m.group(2), m.group(3)
        parsed.append({
            "line_no": idx + 1,
            "event": event,
            "user_id": user_id,
            "ts": float(ts_str),
        })
    return parsed


def test_log_file_exists_and_has_eight_entries():
    entries = _parse_log()
    assert len(entries) == 8, (
        f"Expected exactly 8 log entries (4 start + 4 end), found "
        f"{len(entries)} in {LOG_PATH}."
    )


def test_entry_counts_per_user_and_event():
    entries = _parse_log()
    counts = {}
    for e in entries:
        counts[(e["user_id"], e["event"])] = counts.get(
            (e["user_id"], e["event"]), 0
        ) + 1
    for user_id in ("A", "B"):
        for event in ("start", "end"):
            assert counts.get((user_id, event), 0) == 2, (
                f"Expected exactly 2 '{event}' entries for user_id={user_id}, "
                f"found {counts.get((user_id, event), 0)}. Full counts: "
                f"{counts}"
            )


def _intervals_for_user(entries, user_id):
    """Pair up the user's start/end events into intervals.

    The task body writes 'start' then 'end' for the same run sequentially with
    a real (~2s) sleep in between. Because the per-key concurrency limit is 1,
    the only valid arrangement is that within a single user_id, the events
    appear in the file in the order: start_1, end_1, start_2, end_2 (no
    interleaving). We pair them in occurrence order accordingly.
    """
    user_events = [e for e in entries if e["user_id"] == user_id]
    starts = [e for e in user_events if e["event"] == "start"]
    ends = [e for e in user_events if e["event"] == "end"]
    assert len(starts) == 2 and len(ends) == 2, (
        f"Expected 2 starts and 2 ends for user_id={user_id}, got "
        f"{len(starts)} starts and {len(ends)} ends."
    )
    # Pair start_i with the earliest end whose timestamp is >= start_i.
    intervals = []
    remaining_ends = sorted(ends, key=lambda e: e["ts"])
    for s in sorted(starts, key=lambda e: e["ts"]):
        match = None
        for re_idx, end in enumerate(remaining_ends):
            if end["ts"] >= s["ts"]:
                match = end
                del remaining_ends[re_idx]
                break
        assert match is not None, (
            f"Could not pair start at ts={s['ts']} for user_id={user_id} "
            f"with any end event (no end has ts >= start)."
        )
        intervals.append((s["ts"], match["ts"]))
    # Sort intervals by start time for downstream non-overlap check.
    intervals.sort(key=lambda iv: iv[0])
    return intervals


def test_user_a_intervals_do_not_overlap():
    entries = _parse_log()
    intervals = _intervals_for_user(entries, "A")
    (s1, e1), (s2, e2) = intervals
    assert e1 - s1 >= 0, f"Interval 1 for A has negative duration: {intervals}"
    assert e2 - s2 >= 0, f"Interval 2 for A has negative duration: {intervals}"
    assert s2 + NON_OVERLAP_TOLERANCE_S >= e1, (
        f"User_id=A intervals overlap: interval1 ends at {e1}, interval2 "
        f"starts at {s2}. Per-key concurrency (max_runs=1) should have "
        f"serialized them. Intervals: {intervals}"
    )


def test_user_b_intervals_do_not_overlap():
    entries = _parse_log()
    intervals = _intervals_for_user(entries, "B")
    (s1, e1), (s2, e2) = intervals
    assert e1 - s1 >= 0, f"Interval 1 for B has negative duration: {intervals}"
    assert e2 - s2 >= 0, f"Interval 2 for B has negative duration: {intervals}"
    assert s2 + NON_OVERLAP_TOLERANCE_S >= e1, (
        f"User_id=B intervals overlap: interval1 ends at {e1}, interval2 "
        f"starts at {s2}. Per-key concurrency (max_runs=1) should have "
        f"serialized them. Intervals: {intervals}"
    )


def test_per_user_total_sleep_time_observed():
    """The sleeps must really happen — total duration per user must be near
    2 * sleep_duration_seconds."""
    entries = _parse_log()
    for user_id in ("A", "B"):
        intervals = _intervals_for_user(entries, user_id)
        total = sum(e - s for s, e in intervals)
        threshold = 2 * SLEEP_DURATION_SECONDS * 0.8
        assert total >= threshold, (
            f"Total interval duration for user_id={user_id} is {total:.3f}s, "
            f"expected at least {threshold:.3f}s (2 runs x ~{SLEEP_DURATION_SECONDS}s). "
            f"This suggests the task did not actually sleep / do work."
        )


def test_cross_user_runs_overlap_in_time():
    """A-runs and B-runs must have executed concurrently, otherwise the
    per-key concurrency strategy was not actually applied (i.e., everything
    serialized globally)."""
    entries = _parse_log()
    all_ts = [e["ts"] for e in entries]
    total_span = max(all_ts) - min(all_ts)
    upper_bound = 4 * SLEEP_DURATION_SECONDS * 0.9
    assert total_span < upper_bound, (
        f"Total wall-clock span across all 8 log entries is {total_span:.3f}s, "
        f"which is >= {upper_bound:.3f}s. That suggests all four runs ran "
        f"sequentially instead of A-runs and B-runs running in parallel. The "
        f"concurrency strategy is likely too restrictive (e.g., a global "
        f"concurrency limit instead of a per-user_id key)."
    )
