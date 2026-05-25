import os
import time

import pytest

LOG_FILE = "/home/user/myproject/output.log"


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _workflow_name() -> str:
    return f"flaky-task-{_run_id()}"


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."


def test_log_file_contains_each_attempt_line():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for n in (0, 1, 2):
        marker = f"Attempt retry_count={n}"
        assert marker in content, (
            f"Expected log file {LOG_FILE} to contain the line '{marker}', "
            f"but it was not found. Log contents:\n{content}"
        )


def test_log_file_contains_success_line():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    expected = "Task succeeded after 3 attempts"
    assert expected in content, (
        f"Expected log file {LOG_FILE} to contain the final outcome line "
        f"'{expected}', but it was not found. Log contents:\n{content}"
    )


def test_hatchet_workflow_succeeded_with_three_attempts():
    """Query the real Hatchet server via the Python SDK and verify the workflow
    run for `flaky-task-${ZEALT_RUN_ID}` succeeded with exactly 3 attempts
    (i.e. 2 retries occurred before success)."""
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
    status_str = getattr(status, "value", status)
    assert str(status_str).upper() in {"SUCCEEDED", "COMPLETED", "SUCCESS"}, (
        f"Expected latest run of '{workflow_name}' to have succeeded, got status={status_str}."
    )

    # 3. Confirm the run had exactly 3 attempts (the initial attempt plus 2 retries).
    tasks = getattr(latest, "tasks", None) or []
    attempts: int | None = None
    if tasks:
        first = tasks[0]
        attempts = (
            getattr(first, "attempt", None)
            or getattr(first, "attempt_number", None)
            or getattr(first, "retry_count", None)
        )
        if attempts is not None and getattr(first, "retry_count", None) == attempts:
            # `retry_count` is zero-indexed; convert to attempt count.
            attempts = attempts + 1

    if attempts is None:
        # Fallback: ask the SDK for the run detail and look at the events / task runs.
        run_id = getattr(latest, "metadata", None)
        run_id = getattr(run_id, "id", None) if run_id is not None else getattr(latest, "id", None)
        assert run_id, "Could not resolve the latest run id from the Hatchet SDK response."
        detail = hatchet.runs.get(run_id)
        detail_tasks = getattr(detail, "tasks", None) or getattr(detail, "task_runs", None) or []
        assert detail_tasks, f"Run {run_id} has no task runs to inspect for attempt count."
        first = detail_tasks[0]
        rc = getattr(first, "retry_count", None)
        if rc is None:
            rc = getattr(first, "attempt", None)
        assert rc is not None, f"Could not determine attempt count for run {run_id}."
        attempts = rc + 1 if getattr(first, "retry_count", None) is not None else rc

    assert attempts == 3, (
        f"Expected workflow '{workflow_name}' to have completed in exactly 3 attempts "
        f"(2 retries + 1 success), but observed {attempts} attempt(s)."
    )
