import os
import re
import time

import pytest

LOG_FILE = "/home/user/myproject/output.log"


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _workflow_name() -> str:
    return f"slow-task-{_run_id()}"


def _read_log() -> str:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."


def test_log_file_contains_run_id_line():
    content = _read_log()
    expected = f"Run ID: {_run_id()}"
    assert expected in content, (
        f"Expected log file {LOG_FILE} to contain the line '{expected}', "
        f"but it was not found. Log contents:\n{content}"
    )


def test_log_file_run_duration_is_approximately_three_seconds():
    """Parse Start and End lines and confirm the run was cancelled at ~3s rather
    than allowed to run the full 10s."""
    content = _read_log()

    start_match = re.search(r"^Start:\s*([0-9]+(?:\.[0-9]+)?)\s*$", content, re.MULTILINE)
    end_match = re.search(r"^End:\s*([0-9]+(?:\.[0-9]+)?)\s*$", content, re.MULTILINE)
    assert start_match, (
        f"Expected log file {LOG_FILE} to contain a 'Start: <unix_epoch_seconds>' line, "
        f"but it was not found. Log contents:\n{content}"
    )
    assert end_match, (
        f"Expected log file {LOG_FILE} to contain an 'End: <unix_epoch_seconds>' line, "
        f"but it was not found. Log contents:\n{content}"
    )
    start_ts = float(start_match.group(1))
    end_ts = float(end_match.group(1))
    duration = end_ts - start_ts
    assert 2.0 <= duration <= 8.0, (
        f"Expected the task to be cancelled at ~3s due to execution_timeout, "
        f"but observed duration was {duration:.2f}s (Start={start_ts}, End={end_ts}). "
        f"This indicates the task was either not cancelled by the 3s execution timeout, "
        f"or the timing was not recorded around the actual task run."
    )


def test_log_file_contains_outcome_indicating_failure_or_cancellation():
    content = _read_log()
    outcome_match = re.search(r"^Outcome:\s*(.+?)\s*$", content, re.MULTILINE)
    assert outcome_match, (
        f"Expected log file {LOG_FILE} to contain an 'Outcome: <status>' line, "
        f"but it was not found. Log contents:\n{content}"
    )
    outcome = outcome_match.group(1).strip().upper()
    acceptable = {"FAILED", "CANCELLED", "CANCELED", "TIMED_OUT", "TIMEOUT"}
    assert any(token in outcome for token in acceptable), (
        f"Expected the Outcome line to indicate a non-success terminal status "
        f"(one of {sorted(acceptable)}), but got: '{outcome}'."
    )


def test_hatchet_workflow_did_not_succeed():
    """Query the real Hatchet server via the Python SDK and confirm the run for
    `slow-task-${ZEALT_RUN_ID}` ended in a non-success terminal state."""
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."

    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    workflow_name = _workflow_name()

    # 1. Locate the workflow by name.
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

    # 2. Find the most recent run for that workflow, retrying briefly to allow
    #    the server to finalize the run state.
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
    assert run_rows, f"Hatchet workflow '{workflow_name}' has no recorded runs."
    latest = run_rows[0]

    status = getattr(latest, "status", None)
    status_str = str(getattr(status, "value", status)).upper()

    success_terms = {"SUCCEEDED", "SUCCESS", "COMPLETED"}
    failure_terms = ("FAIL", "CANCEL", "TIMEOUT", "TIMED_OUT", "ERROR")
    assert status_str not in success_terms, (
        f"Expected latest run of '{workflow_name}' to NOT be a success terminal status, "
        f"but observed status={status_str}. The task body sleeps 10s with execution_timeout=3s, "
        f"so it must be cancelled, not succeeded."
    )
    assert any(term in status_str for term in failure_terms), (
        f"Expected latest run of '{workflow_name}' to be in a failure-like terminal state "
        f"(one of {failure_terms}), but observed status={status_str}."
    )
