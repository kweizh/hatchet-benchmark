import os
import re
import pytest


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


def _log_path() -> str:
    return f"/tmp/prio_log_{_run_id()}.txt"


def _read_lines():
    path = _log_path()
    assert os.path.isfile(path), f"Expected log file at {path} to exist after the task runs."
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return lines


def _parse_line(line: str):
    parts = line.split()
    assert len(parts) == 2, (
        f"Each log line must have exactly two whitespace-separated tokens (<priority> <epoch_ms>); got: {line!r}"
    )
    prio_tok, ts_tok = parts
    assert re.fullmatch(r"\d+", prio_tok), f"Priority token must be an integer, got: {prio_tok!r}"
    assert re.fullmatch(r"\d+", ts_tok), f"Epoch-ms token must be an integer, got: {ts_tok!r}"
    prio = int(prio_tok)
    ts = int(ts_tok)
    assert prio in (1, 3), f"Priority must be 1 or 3, got: {prio}"
    assert ts > 0, f"Epoch-ms must be a positive integer, got: {ts}"
    return prio, ts


def test_log_file_exists_and_has_five_lines():
    lines = _read_lines()
    assert len(lines) == 5, f"Expected exactly 5 non-empty log lines, got {len(lines)}: {lines!r}"


def test_log_lines_have_correct_format():
    lines = _read_lines()
    for line in lines:
        _parse_line(line)


def test_timestamps_are_monotonic_non_decreasing():
    lines = _read_lines()
    timestamps = [_parse_line(line)[1] for line in lines]
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i - 1], (
            f"Log timestamps must be non-decreasing (execution order). "
            f"Line {i} ts {timestamps[i]} < line {i - 1} ts {timestamps[i - 1]}. All lines: {lines!r}"
        )


def test_priority_multiset_three_lows_two_highs():
    lines = _read_lines()
    priorities = [_parse_line(line)[0] for line in lines]
    lows = priorities.count(1)
    highs = priorities.count(3)
    assert lows == 3 and highs == 2, (
        f"Expected exactly three priority-1 (low) entries and two priority-3 (high) entries; "
        f"got lows={lows}, highs={highs}. Priorities: {priorities}"
    )


def test_priority_reordering_after_first_run():
    lines = _read_lines()
    priorities = [_parse_line(line)[0] for line in lines]
    tail = priorities[1:]  # lines 2..5
    # All priority-3 entries within the tail must appear before any priority-1 entry.
    high_indices = [i for i, p in enumerate(tail) if p == 3]
    low_indices = [i for i, p in enumerate(tail) if p == 1]
    if high_indices and low_indices:
        assert max(high_indices) < min(low_indices), (
            "Within lines 2..5 (after the first executed run), all priority-3 (high) entries "
            f"must come before any priority-1 (low) entries. Tail priorities: {tail}"
        )


def test_hatchet_token_present_for_runtime():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN must remain set so that Hatchet Cloud is reachable."
