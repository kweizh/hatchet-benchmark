import json
import os
import re
import time

import pytest


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
TIMELINE_FILE = os.path.join(PROJECT_DIR, "timeline.jsonl")

EXPECTED_PAIRS = {("alice", 1), ("alice", 2), ("bob", 1), ("bob", 2)}
RUN_LINE_RE = re.compile(
    r"^Run user_id=(?P<user_id>\S+) op_id=(?P<op_id>\d+) run_id=(?P<run_id>\S+)\s*$"
)


def _run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "Environment variable ZEALT_RUN_ID must be set for verification."
    return rid


_timeline_cache = None
_log_cache = None


def _load_timeline():
    global _timeline_cache
    if _timeline_cache is not None:
        return _timeline_cache
    assert os.path.isfile(TIMELINE_FILE), (
        f"Expected timeline file {TIMELINE_FILE} to exist after the task completes."
    )
    records = []
    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        for i, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(
                    f"Line {i} of {TIMELINE_FILE} is not valid JSON: {e}. Content: {line!r}"
                )
            records.append(rec)
    _timeline_cache = records
    return records


def _load_log_lines():
    global _log_cache
    if _log_cache is not None:
        return _log_cache
    assert os.path.isfile(LOG_FILE), (
        f"Expected project log file {LOG_FILE} to exist after the task completes."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        _log_cache = [ln.rstrip("\n") for ln in f.readlines()]
    return _log_cache


def _parse_run_lines():
    """Return {(user_id, op_id): run_id} parsed from the project log file."""
    mapping = {}
    for ln in _load_log_lines():
        m = RUN_LINE_RE.match(ln.strip())
        if not m:
            continue
        key = (m.group("user_id"), int(m.group("op_id")))
        mapping[key] = m.group("run_id")
    return mapping


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected project log file {LOG_FILE} to exist after the task completes."
    )


def test_timeline_file_exists():
    assert os.path.isfile(TIMELINE_FILE), (
        f"Expected timeline file {TIMELINE_FILE} to exist after the task completes."
    )


def test_timeline_has_four_records_with_required_fields():
    records = _load_timeline()
    assert len(records) == 4, (
        f"Expected exactly 4 timeline records in {TIMELINE_FILE}, got {len(records)}.\n"
        f"Records: {records}"
    )
    for idx, rec in enumerate(records):
        for key in ("user_id", "op_id", "start_ts", "end_ts"):
            assert key in rec, (
                f"Record {idx} of {TIMELINE_FILE} is missing required key {key!r}: {rec}"
            )
        assert isinstance(rec["user_id"], str) and rec["user_id"], (
            f"Record {idx} has invalid user_id: {rec}"
        )
        assert isinstance(rec["op_id"], int) and not isinstance(rec["op_id"], bool), (
            f"Record {idx} op_id must be an int, got {type(rec["op_id"]).__name__}: {rec}"
        )
        assert isinstance(rec["start_ts"], (int, float)) and not isinstance(
            rec["start_ts"], bool
        ), f"Record {idx} start_ts must be numeric, got {rec["start_ts"]!r}"
        assert isinstance(rec["end_ts"], (int, float)) and not isinstance(
            rec["end_ts"], bool
        ), f"Record {idx} end_ts must be numeric, got {rec["end_ts"]!r}"
        duration = float(rec["end_ts"]) - float(rec["start_ts"])
        assert duration >= 2.0, (
            f"Record {idx} duration must be >= 2.0s (task sleeps at least 2s), "
            f"got {duration:.3f}s. Record: {rec}"
        )


def test_timeline_covers_expected_user_op_pairs():
    records = _load_timeline()
    pairs = {(r["user_id"], int(r["op_id"])) for r in records}
    assert pairs == EXPECTED_PAIRS, (
        f"Expected timeline to cover exactly {sorted(EXPECTED_PAIRS)} but got "
        f"{sorted(pairs)}."
    )


def test_per_key_serialization_alice():
    records = _load_timeline()
    alice = sorted(
        [r for r in records if r["user_id"] == "alice"],
        key=lambda r: float(r["start_ts"]),
    )
    assert len(alice) == 2, f"Expected 2 alice records, got {len(alice)}: {alice}"
    first_end = float(alice[0]["end_ts"])
    second_start = float(alice[1]["start_ts"])
    assert second_start >= first_end - 0.25, (
        "Hatchet should serialize same-user runs via the GROUP_ROUND_ROBIN "
        f"concurrency strategy, but the two alice runs overlapped: "
        f"first=({alice[0]["start_ts"]}, {alice[0]["end_ts"]}) "
        f"second=({alice[1]["start_ts"]}, {alice[1]["end_ts"]})."
    )


def test_per_key_serialization_bob():
    records = _load_timeline()
    bob = sorted(
        [r for r in records if r["user_id"] == "bob"],
        key=lambda r: float(r["start_ts"]),
    )
    assert len(bob) == 2, f"Expected 2 bob records, got {len(bob)}: {bob}"
    first_end = float(bob[0]["end_ts"])
    second_start = float(bob[1]["start_ts"])
    assert second_start >= first_end - 0.25, (
        "Hatchet should serialize same-user runs via the GROUP_ROUND_ROBIN "
        f"concurrency strategy, but the two bob runs overlapped: "
        f"first=({bob[0]["start_ts"]}, {bob[0]["end_ts"]}) "
        f"second=({bob[1]["start_ts"]}, {bob[1]["end_ts"]})."
    )


def test_cross_key_parallelism():
    records = _load_timeline()
    alices = [r for r in records if r["user_id"] == "alice"]
    bobs = [r for r in records if r["user_id"] == "bob"]
    assert alices and bobs, "Need at least one alice and one bob record."
    overlap_found = False
    for a in alices:
        a_s, a_e = float(a["start_ts"]), float(a["end_ts"])
        for b in bobs:
            b_s, b_e = float(b["start_ts"]), float(b["end_ts"])
            if min(a_e, b_e) > max(a_s, b_s):
                overlap_found = True
                break
        if overlap_found:
            break
    assert overlap_found, (
        "Expected at least one alice run and one bob run to overlap in time "
        "(Hatchet should only serialize runs that share a concurrency key). "
        f"Alice intervals: {[(a["start_ts"], a["end_ts"]) for a in alices]} "
        f"Bob intervals: {[(b["start_ts"], b["end_ts"]) for b in bobs]}."
    )


def test_log_file_contains_all_four_run_lines():
    mapping = _parse_run_lines()
    missing = [pair for pair in EXPECTED_PAIRS if pair not in mapping]
    assert not missing, (
        f"Expected project log file {LOG_FILE} to contain a "
        f"Run user_id=<u> op_id=<n> run_id=<id> line for every expected pair. "
        f"Missing: {missing}. Parsed mapping: {mapping}."
    )
    for key, run_id in mapping.items():
        assert run_id and isinstance(run_id, str), (
            f"Run id for {key} is empty/invalid in the project log: {run_id!r}"
        )


def test_log_file_contains_completion_summary():
    lines = _load_log_lines()
    expected = "All 4 runs completed"
    assert any(expected in ln for ln in lines), (
        f"Expected the project log file {LOG_FILE} to contain a summary line "
        f"\u0027{expected}\u0027, but it was not found. Log contents:\n" + "\n".join(lines)
    )


def _hatchet_client():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."
    from hatchet_sdk import Hatchet

    return Hatchet()


def _extract_output(detail):
    """Walk a runs.get(...) detail object looking for the task output payload."""
    direct = getattr(detail, "output", None)
    if isinstance(direct, dict) and direct:
        return direct
    if isinstance(detail, dict):
        if isinstance(detail.get("output"), dict) and detail["output"]:
            return detail["output"]
        tasks = detail.get("tasks") or detail.get("task_runs") or []
    else:
        tasks = getattr(detail, "tasks", None) or getattr(detail, "task_runs", None) or []
    for t in tasks:
        if isinstance(t, dict):
            out = t.get("output")
        else:
            out = getattr(t, "output", None)
        if isinstance(out, dict) and out:
            return out
        if isinstance(out, str):
            try:
                parsed = json.loads(out)
                if isinstance(parsed, dict):
                    return parsed
            except (ValueError, TypeError):
                pass
    return None


def _get_status_str(detail):
    if isinstance(detail, dict):
        s = detail.get("status")
    else:
        s = getattr(detail, "status", None)
    if s is None:
        return None
    return str(getattr(s, "value", s)).upper()


def test_runs_status_succeeded_and_outputs_match_via_sdk():
    hatchet = _hatchet_client()
    mapping = _parse_run_lines()
    assert mapping, "No run_id lines parsed from project log; cannot query Hatchet."

    timeline_by_pair = {
        (r["user_id"], int(r["op_id"])): r for r in _load_timeline()
    }

    failures = []
    for (user_id, op_id), run_id in mapping.items():
        timeline_rec = timeline_by_pair.get((user_id, op_id))
        if timeline_rec is None:
            failures.append(
                f"{user_id}/{op_id} run_id={run_id}: no matching timeline record."
            )
            continue

        output = None
        last_err = None
        deadline = time.time() + 60
        while time.time() < deadline and output is None:
            try:
                if hasattr(hatchet.runs, "get_result"):
                    res = hatchet.runs.get_result(run_id)
                    if isinstance(res, dict) and res:
                        output = res
                    elif res is not None:
                        output = _extract_output(res) or (
                            res if isinstance(res, dict) else None
                        )
                if output is None:
                    detail = hatchet.runs.get(run_id)
                    output = _extract_output(detail)
                    status_str = _get_status_str(detail)
                    if status_str and status_str not in {
                        "SUCCEEDED",
                        "COMPLETED",
                        "SUCCESS",
                    }:
                        if status_str in {"RUNNING", "QUEUED", "PENDING", "SCHEDULED"}:
                            output = None
                if output is not None:
                    break
            except Exception as e:  # noqa: BLE001
                last_err = e
            time.sleep(2)

        if output is None:
            failures.append(
                f"{user_id}/{op_id} run_id={run_id}: could not retrieve output "
                f"payload from Hatchet (last_err={last_err})."
            )
            continue

        try:
            detail = hatchet.runs.get(run_id)
            status_str = _get_status_str(detail)
            if status_str is not None:
                assert status_str in {"SUCCEEDED", "COMPLETED", "SUCCESS"}, (
                    f"{user_id}/{op_id} run_id={run_id}: expected terminal "
                    f"success status, got {status_str}."
                )
        except AssertionError:
            raise
        except Exception:
            pass

        out_user = output.get("user_id")
        out_op = output.get("op_id")
        out_start = output.get("start_ts")
        out_end = output.get("end_ts")

        if out_user != user_id or int(out_op) != op_id:
            failures.append(
                f"{user_id}/{op_id} run_id={run_id}: Hatchet output payload "
                f"mismatch user_id/op_id (got user_id={out_user!r}, op_id={out_op!r})."
            )
            continue

        try:
            if abs(float(out_start) - float(timeline_rec["start_ts"])) > 0.5:
                failures.append(
                    f"{user_id}/{op_id} run_id={run_id}: start_ts mismatch "
                    f"timeline={timeline_rec["start_ts"]} vs Hatchet={out_start}."
                )
                continue
            if abs(float(out_end) - float(timeline_rec["end_ts"])) > 0.5:
                failures.append(
                    f"{user_id}/{op_id} run_id={run_id}: end_ts mismatch "
                    f"timeline={timeline_rec["end_ts"]} vs Hatchet={out_end}."
                )
                continue
        except (TypeError, ValueError) as e:
            failures.append(
                f"{user_id}/{op_id} run_id={run_id}: cannot compare timestamps ({e}). "
                f"Output: {output}"
            )

    assert not failures, "Hatchet SDK verification failures:\n - " + "\n - ".join(failures)
