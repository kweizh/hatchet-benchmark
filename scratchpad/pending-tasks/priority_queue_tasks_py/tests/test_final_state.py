import os
import time

import pytest


LOG_FILE = "/home/user/myproject/output.log"

EXPECTED_IDS = {"low-1", "low-2", "low-3", "high-1", "high-2", "high-3"}


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _workflow_name() -> str:
    return f"priority-task-{_run_id()}"


def _read_log_lines() -> list[str]:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    return lines


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."


def test_log_file_has_exactly_six_expected_ids():
    lines = _read_log_lines()
    assert len(lines) == 6, (
        f"Expected exactly 6 non-empty lines in {LOG_FILE}, got {len(lines)}. Lines: {lines!r}"
    )
    assert set(lines) == EXPECTED_IDS, (
        f"Expected the log to contain exactly the ids {sorted(EXPECTED_IDS)} (each once), "
        f"but got {sorted(lines)}."
    )
    # Each id should appear exactly once.
    for expected_id in EXPECTED_IDS:
        assert lines.count(expected_id) == 1, (
            f"Expected id '{expected_id}' to appear exactly once in {LOG_FILE}, "
            f"got {lines.count(expected_id)} occurrence(s)."
        )


def test_log_file_priority_ordering_respected():
    """Verify that Hatchet's priority queue picked HIGH-priority runs before LOW-priority runs.

    To allow for the documented exception (one LOW run may have already begun executing
    when the HIGH runs were enqueued), the check is:
      - the last two entries MUST both be LOW, AND
      - among the first four entries, AT LEAST three MUST be HIGH.
    """
    lines = _read_log_lines()
    assert len(lines) == 6, (
        f"Expected exactly 6 lines in {LOG_FILE} for ordering check, got {len(lines)}. Lines: {lines!r}"
    )

    def classify(line: str) -> str:
        if line.startswith("high-"):
            return "HIGH"
        if line.startswith("low-"):
            return "LOW"
        raise AssertionError(f"Unexpected log line that is neither HIGH nor LOW: {line!r}")

    priorities = [classify(ln) for ln in lines]

    last_two = priorities[-2:]
    assert last_two == ["LOW", "LOW"], (
        f"Expected the last two executions in the log to be LOW priority "
        f"(HIGH-priority runs should drain first), got {last_two}. Full order: {priorities}."
    )

    first_four_high_count = priorities[:4].count("HIGH")
    assert first_four_high_count >= 3, (
        f"Expected at least 3 of the first 4 executions to be HIGH priority "
        f"(one LOW may already have been running when HIGHs were enqueued), "
        f"got {first_four_high_count} HIGH in {priorities[:4]}. Full order: {priorities}."
    )


def test_hatchet_workflow_recorded_runs_on_server():
    """Connect to the real Hatchet server and confirm that at least six runs of the
    priority-task workflow exist for this trial, proving the runs were executed against
    the real backend (not only locally appended to the log file)."""
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."

    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    workflow_name = _workflow_name()

    # 1. Locate the workflow by name (retry briefly to allow registration to settle).
    workflow = None
    deadline = time.time() + 30
    available_names: list = []
    while time.time() < deadline:
        workflows = hatchet.workflows.list()
        rows = getattr(workflows, "rows", None) or []
        available_names = [getattr(w, "name", None) for w in rows]
        matching = [w for w in rows if getattr(w, "name", None) == workflow_name]
        if matching:
            workflow = matching[0]
            break
        time.sleep(2)
    assert workflow is not None, (
        f"No Hatchet workflow named '{workflow_name}' was found on the server. "
        f"Workflows available: {available_names}"
    )

    workflow_meta = getattr(workflow, "metadata", None)
    workflow_id = getattr(workflow_meta, "id", None) if workflow_meta is not None else getattr(workflow, "id", None)
    assert workflow_id, f"Could not resolve workflow id for '{workflow_name}'."

    # 2. Fetch recent runs for that workflow and verify at least 6 runs exist.
    runs = None
    last_err: Exception | None = None
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            runs = hatchet.runs.list(workflow_ids=[workflow_id])
            run_rows = getattr(runs, "rows", None) or []
            if len(run_rows) >= 6:
                break
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(2)
    assert runs is not None, f"Failed to list runs for workflow '{workflow_name}': {last_err}"

    run_rows = getattr(runs, "rows", None) or []
    assert len(run_rows) >= 6, (
        f"Expected at least 6 recorded runs for workflow '{workflow_name}' on the Hatchet server, "
        f"got {len(run_rows)}."
    )
