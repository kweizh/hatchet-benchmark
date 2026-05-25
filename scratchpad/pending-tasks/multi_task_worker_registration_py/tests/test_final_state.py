import os
import re

import pytest


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


def _task_names() -> dict:
    run_id = _run_id()
    return {
        "add": f"math-add-{run_id}",
        "subtract": f"math-subtract-{run_id}",
        "multiply": f"math-multiply-{run_id}",
    }


def _read_log() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after task execution."
    )
    with open(LOG_FILE, "r") as f:
        content = f.read()
    assert content.strip(), f"Log file {LOG_FILE} is empty."
    return content


@pytest.mark.parametrize(
    "task_key,expected_result",
    [
        ("add", 13),
        ("subtract", 7),
        ("multiply", 30),
    ],
)
def test_log_contains_task_result(task_key, expected_result):
    """Each task's result (matching the expected math output) must be logged."""
    names = _task_names()
    task_name = names[task_key]
    content = _read_log()
    pattern = re.compile(
        rf"Task\s+{re.escape(task_name)}\s+result:\s+{expected_result}\b"
    )
    assert pattern.search(content), (
        f"Expected log line matching 'Task {task_name} result: {expected_result}' "
        f"in {LOG_FILE}. Actual content:\n{content}"
    )


def test_all_three_tasks_registered_on_hatchet_server():
    """
    Confirm that all three tasks were registered on the real Hatchet server by
    listing the workflows via the hatchet-sdk client.
    """
    import hatchet_sdk  # noqa: F401
    from hatchet_sdk import Hatchet

    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    )
    assert os.environ.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL must be set to query the Hatchet server."
    )

    hatchet = Hatchet(debug=False)
    names = _task_names()
    expected = set(names.values())

    listed_names = set()
    try:
        workflows = hatchet.workflows.list()
    except Exception as exc:
        raise AssertionError(
            f"Failed to list workflows from Hatchet server: {exc}"
        )

    # The list() return value may be a paginated response object or a plain
    # list. Try to be defensive about the shape and extract names.
    rows = getattr(workflows, "rows", None)
    if rows is None:
        rows = getattr(workflows, "workflows", None)
    if rows is None and isinstance(workflows, list):
        rows = workflows
    if rows is None:
        raise AssertionError(
            f"Unexpected workflows.list() response shape: {workflows!r}"
        )

    for row in rows:
        name = getattr(row, "name", None)
        if name is None and isinstance(row, dict):
            name = row.get("name")
        if name:
            listed_names.add(name)

    missing = expected - listed_names
    assert not missing, (
        f"Expected workflows {sorted(expected)} to be registered on the Hatchet "
        f"server, but the following are missing: {sorted(missing)}. "
        f"Actual listed names sample: {sorted(list(listed_names))[:20]}"
    )
