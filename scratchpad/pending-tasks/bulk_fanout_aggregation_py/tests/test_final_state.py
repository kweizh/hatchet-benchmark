import os
import re

import pytest


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
EXPECTED_TOTAL = 420
EXPECTED_RUN_COUNT = 20


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id


def _task_name() -> str:
    return f"process-item-{_run_id()}"


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task ran."
    )


def test_log_file_contains_total_sum():
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        content = fh.read()
    pattern = re.compile(r"^Total sum:\s*(\d+)\s*$", re.MULTILINE)
    match = pattern.search(content)
    assert match is not None, (
        f"Log file {LOG_FILE} does not contain a line matching "
        f"'Total sum: <int>'. File contents:\n{content}"
    )
    actual = int(match.group(1))
    assert actual == EXPECTED_TOTAL, (
        f"Expected 'Total sum: {EXPECTED_TOTAL}' in {LOG_FILE}, got "
        f"'Total sum: {actual}'."
    )


@pytest.fixture(scope="module")
def hatchet_client():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."
    assert server_url, "HATCHET_SERVER_URL environment variable is not set."

    from hatchet_sdk import Hatchet

    return Hatchet()


def test_workflow_registered_with_run_id_suffix(hatchet_client):
    task_name = _task_name()
    workflows = hatchet_client.workflows.list(workflow_name=task_name)
    rows = getattr(workflows, "rows", None) or []
    matching = [w for w in rows if w.name == task_name]
    assert matching, (
        f"Expected at least one workflow registered with name '{task_name}'. "
        f"Found workflows: {[w.name for w in rows]}"
    )


def test_at_least_twenty_completed_runs(hatchet_client):
    from hatchet_sdk.clients.rest.models.v1_task_status import V1TaskStatus

    task_name = _task_name()

    workflows = hatchet_client.workflows.list(workflow_name=task_name)
    rows = getattr(workflows, "rows", None) or []
    matching = [w for w in rows if w.name == task_name]
    assert matching, (
        f"Cannot verify runs because workflow '{task_name}' was not found."
    )
    workflow_id = matching[0].metadata.id

    runs = hatchet_client.runs.list(
        workflow_ids=[workflow_id],
        statuses=[V1TaskStatus.COMPLETED],
        limit=100,
    )
    run_rows = getattr(runs, "rows", None) or []
    assert len(run_rows) >= EXPECTED_RUN_COUNT, (
        f"Expected at least {EXPECTED_RUN_COUNT} COMPLETED runs of workflow "
        f"'{task_name}' (id={workflow_id}), found {len(run_rows)}."
    )
