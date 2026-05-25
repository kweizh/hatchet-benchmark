import os
import re
import time

import pytest

LOG_FILE = "/home/user/myproject/stream.log"
EXPECTED_LINES = [
    "progress: 1/5",
    "progress: 2/5",
    "progress: 3/5",
    "progress: 4/5",
    "progress: 5/5",
]


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _workflow_name() -> str:
    return f"progress-counter-{_run_id()}"


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task completes."
    )


def test_log_file_contains_expected_progress_lines_in_order():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f.readlines()]

    # Filter out empty lines, but preserve order of progress-style lines.
    progress_pattern = re.compile(r"^progress:\s*\d+/\d+$")
    progress_lines = [line for line in raw_lines if progress_pattern.match(line)]

    assert progress_lines == EXPECTED_LINES, (
        f"Expected {LOG_FILE} to contain exactly these progress lines in this order:\n"
        f"{EXPECTED_LINES}\n"
        f"But found:\n{progress_lines}\n"
        f"Full file contents:\n{open(LOG_FILE, 'r', encoding='utf-8').read()}"
    )


def test_hatchet_workflow_succeeded():
    """Query the real Hatchet server via the Python SDK and verify the latest
    workflow run for `progress-counter-${ZEALT_RUN_ID}` reached a terminal
    SUCCEEDED status."""
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
    workflow_id = (
        getattr(workflow_id, "id", None)
        if workflow_id is not None
        else getattr(workflow, "id", None)
    )
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
    assert runs is not None, (
        f"Failed to list runs for workflow '{workflow_name}': {last_err}"
    )

    run_rows = getattr(runs, "rows", None) or []
    assert run_rows, f"Hatchet workflow '{workflow_name}' has no recorded runs."
    latest = run_rows[0]

    status = getattr(latest, "status", None)
    status_str = getattr(status, "value", status)
    assert str(status_str).upper() in {"SUCCEEDED", "COMPLETED", "SUCCESS"}, (
        f"Expected latest run of '{workflow_name}' to have succeeded, "
        f"got status={status_str}."
    )
