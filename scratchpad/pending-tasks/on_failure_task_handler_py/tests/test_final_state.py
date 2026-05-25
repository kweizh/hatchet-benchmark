import os
import re

import pytest

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

TRIGGERED_RE = re.compile(r"^Triggered run_id=(.+)$", re.MULTILINE)
CLEANUP_RE = re.compile(r"^Cleanup ran for run_id=(.+)$", re.MULTILINE)


@pytest.fixture(scope="session")
def log_contents():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task ran."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        content = fh.read()
    assert content.strip(), f"Log file {LOG_FILE} is empty; expected cleanup output."
    return content


@pytest.fixture(scope="session")
def triggered_run_id(log_contents):
    matches = TRIGGERED_RE.findall(log_contents)
    assert matches, (
        "Expected a line matching 'Triggered run_id=<id>' in the log file, found none."
    )
    assert len(matches) == 1, (
        f"Expected exactly one 'Triggered run_id=' line, found {len(matches)}: {matches!r}"
    )
    run_id = matches[0].strip()
    assert run_id, "Captured triggered run_id is empty."
    return run_id


@pytest.fixture(scope="session")
def cleanup_run_id(log_contents):
    matches = CLEANUP_RE.findall(log_contents)
    assert matches, (
        "Expected a line matching 'Cleanup ran for run_id=<id>' in the log file, found none."
    )
    assert len(matches) == 1, (
        f"Expected exactly one 'Cleanup ran for run_id=' line, found {len(matches)}: {matches!r}"
    )
    run_id = matches[0].strip()
    assert run_id, "Captured cleanup run_id is empty."
    return run_id


def test_triggered_and_cleanup_run_ids_match(triggered_run_id, cleanup_run_id):
    assert triggered_run_id == cleanup_run_id, (
        f"Triggered run_id ({triggered_run_id!r}) does not match the cleanup run_id ({cleanup_run_id!r})."
    )


def test_workflow_run_is_failed_on_hatchet_server(triggered_run_id):
    """Use the Hatchet Python SDK to verify the run exists on the server and is FAILED."""
    run_id_suffix = os.environ.get("ZEALT_RUN_ID")
    assert run_id_suffix, "ZEALT_RUN_ID must be set in the verifier environment."
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set in the verifier environment."
    assert server, "HATCHET_SERVER_URL must be set in the verifier environment."

    from hatchet_sdk import Hatchet  # noqa: WPS433 (import inside test by design)

    hatchet = Hatchet()

    expected_workflow_name = f"failing-flow-{run_id_suffix}"

    # Find the workflow by name.
    workflows = hatchet.workflows.list()
    rows = getattr(workflows, "rows", None) or []
    candidates = [w for w in rows if getattr(w, "name", None) == expected_workflow_name]
    assert candidates, (
        f"Workflow named {expected_workflow_name!r} was not found on the Hatchet server. "
        f"Found workflows: {[getattr(w, 'name', None) for w in rows]!r}"
    )
    workflow = candidates[0]
    workflow_id = getattr(workflow.metadata, "id", None) or getattr(workflow, "id", None)
    assert workflow_id, (
        f"Could not determine workflow id for workflow {expected_workflow_name!r}."
    )

    # List runs for the workflow and locate the triggered one.
    runs = hatchet.runs.list(workflow_ids=[workflow_id])
    run_rows = getattr(runs, "rows", None) or []
    matched = None
    for run in run_rows:
        meta = getattr(run, "metadata", None)
        run_id = getattr(meta, "id", None) if meta is not None else getattr(run, "id", None)
        if run_id == triggered_run_id:
            matched = run
            break

    assert matched is not None, (
        f"Run with id {triggered_run_id!r} was not found among runs of workflow "
        f"{expected_workflow_name!r}. Found run ids: "
        f"{[getattr(getattr(r, 'metadata', None), 'id', None) for r in run_rows]!r}"
    )

    status = getattr(matched, "status", None)
    status_str = str(status).upper() if status is not None else ""
    assert "FAILED" in status_str, (
        f"Expected workflow run {triggered_run_id!r} to have status FAILED, got {status!r}."
    )
