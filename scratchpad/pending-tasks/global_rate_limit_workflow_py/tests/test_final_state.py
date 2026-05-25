import os
import re
import time

import pytest

LOG_FILE = "/home/user/myproject/output.log"

LINE_PATTERN = re.compile(r"^ts=([0-9]+(?:\.[0-9]+)?)\s+run_id=(\S+)\s*$")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _workflow_name() -> str:
    return f"rate-limited-task-{_run_id()}"


def _read_log_lines() -> list[str]:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f.readlines()]


def _parse_records(lines: list[str]) -> list[tuple[float, str]]:
    records: list[tuple[float, str]] = []
    for ln in lines:
        m = LINE_PATTERN.match(ln.strip())
        if m:
            records.append((float(m.group(1)), m.group(2)))
    return records


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."


def test_log_file_has_six_run_records():
    lines = _read_log_lines()
    records = _parse_records(lines)
    assert len(records) == 6, (
        f"Expected exactly 6 log records of the form 'ts=<float> run_id=<id>' in {LOG_FILE}, "
        f"but found {len(records)}. Log contents:\n" + "\n".join(lines)
    )
    run_ids = [r[1] for r in records]
    for rid in run_ids:
        assert rid, f"Found a record with an empty run_id in {LOG_FILE}."
    assert len(set(run_ids)) == 6, (
        f"Expected 6 distinct workflow run ids in {LOG_FILE}, got: {run_ids}"
    )


def test_log_file_contains_done_marker():
    lines = _read_log_lines()
    assert any(ln.strip() == "Done" for ln in lines), (
        f"Expected {LOG_FILE} to contain a final line equal to 'Done'. Log contents:\n"
        + "\n".join(lines)
    )


def test_timestamps_show_rate_limit_throttling():
    """The first 3 runs must be clustered, the 4th must wait for the next bucket window."""
    lines = _read_log_lines()
    records = _parse_records(lines)
    assert len(records) == 6, (
        f"Expected exactly 6 records in {LOG_FILE} but found {len(records)}."
    )
    timestamps = sorted(r[0] for r in records)
    t1, t2, t3, t4, _t5, _t6 = timestamps

    initial_cluster_span = t3 - t1
    assert initial_cluster_span <= 10.0, (
        f"Expected the first 3 runs to be clustered within 10 seconds (consumed initial bucket), "
        f"but the span between t1={t1} and t3={t3} was {initial_cluster_span:.2f} seconds. "
        f"Sorted timestamps: {timestamps}"
    )

    throttled_gap = t4 - t1
    assert throttled_gap >= 30.0, (
        f"Expected the 4th run to be throttled and to start at least 30 seconds after t1 "
        f"(t1={t1}, t4={t4}, gap={throttled_gap:.2f}s). The Hatchet static rate limit "
        f"of 3 per MINUTE was not observed. Sorted timestamps: {timestamps}"
    )


def test_hatchet_runs_succeeded_via_sdk():
    """Query the real Hatchet server via the Python SDK and verify that the workflow
    `rate-limited-task-${ZEALT_RUN_ID}` has at least 6 successful runs."""
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."

    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    workflow_name = _workflow_name()

    workflows = hatchet.workflows.list()
    rows = getattr(workflows, "rows", None) or []
    matching = [w for w in rows if getattr(w, "name", None) == workflow_name]
    assert matching, (
        f"No Hatchet workflow named '{workflow_name}' was found on the server. "
        f"Workflows available: {[getattr(w, 'name', None) for w in rows]}"
    )
    workflow = matching[0]
    workflow_id = getattr(workflow, "metadata", None)
    workflow_id = getattr(workflow_id, "id", None) if workflow_id is not None else getattr(workflow, "id", None)
    assert workflow_id, f"Could not resolve workflow id for '{workflow_name}'."

    runs = None
    deadline = time.time() + 60
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            runs = hatchet.runs.list(workflow_ids=[workflow_id])
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2)
    assert runs is not None, f"Failed to list runs for workflow '{workflow_name}': {last_err}"

    run_rows = getattr(runs, "rows", None) or []
    assert len(run_rows) >= 6, (
        f"Expected at least 6 runs for workflow '{workflow_name}', found {len(run_rows)}."
    )

    success_states = {"SUCCEEDED", "COMPLETED", "SUCCESS"}
    latest_six = run_rows[:6]
    for run in latest_six:
        status = getattr(run, "status", None)
        status_str = str(getattr(status, "value", status)).upper()
        assert status_str in success_states, (
            f"Expected the 6 most recent runs of '{workflow_name}' to all have a terminal "
            f"success status (one of {success_states}), but observed status={status_str}."
        )
