import os
import re
import pytest

LOG_FILE = "/home/user/myproject/output.log"


@pytest.fixture(scope="session")
def run_id() -> str:
    value = os.environ.get("ZEALT_RUN_ID", "")
    assert value, "ZEALT_RUN_ID environment variable is not set."
    return value


@pytest.fixture(scope="session")
def parent_task_name(run_id: str) -> str:
    return f"fanout-parent-{run_id}"


@pytest.fixture(scope="session")
def child_task_name(run_id: str) -> str:
    return f"fanout-child-{run_id}"


@pytest.fixture(scope="session")
def log_contents() -> str:
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        return f.read()


@pytest.fixture(scope="session")
def logged_workflow_run_id(log_contents: str) -> str:
    match = re.search(r"^\s*Run ID:\s*(\S+)\s*$", log_contents, re.MULTILINE)
    assert match, (
        f"Could not find a line matching 'Run ID: <id>' in {LOG_FILE}. "
        f"Log contents:\n{log_contents}"
    )
    return match.group(1)


@pytest.fixture(scope="session")
def hatchet_client():
    # Ensure the SDK can be imported and a client can be constructed using
    # the existing HATCHET_CLIENT_TOKEN / HATCHET_SERVER_URL env vars.
    try:
        from hatchet_sdk import Hatchet
    except ImportError as e:
        pytest.fail(f"Failed to import hatchet_sdk: {e}")
    return Hatchet()


def _status_to_str(status) -> str:
    """Return an upper-case string representation of a status value."""
    if status is None:
        return ""
    # Enum or pydantic-like
    value = getattr(status, "value", status)
    return str(value).upper()


def _is_successful(status) -> bool:
    s = _status_to_str(status)
    return s in {"SUCCEEDED", "COMPLETED", "SUCCESS"}


def test_log_file_exists_and_contains_run_id(log_contents: str):
    """The log file must record the parent workflow run ID."""
    assert re.search(r"^\s*Run ID:\s*\S+\s*$", log_contents, re.MULTILINE), (
        f"Log file {LOG_FILE} does not contain a 'Run ID: <id>' line. "
        f"Contents:\n{log_contents}"
    )


def test_log_file_contains_total_55(log_contents: str):
    """The log file must record the aggregated total of 55."""
    assert re.search(r"^\s*Total:\s*55\s*$", log_contents, re.MULTILINE), (
        f"Log file {LOG_FILE} does not contain a 'Total: 55' line. "
        f"Contents:\n{log_contents}"
    )


def test_parent_and_child_workflows_registered_on_server(
    hatchet_client, parent_task_name: str, child_task_name: str
):
    """The parent and child workflows must be registered on the real Hatchet server."""
    workflows = hatchet_client.workflows.list()
    rows = getattr(workflows, "rows", None) or []
    names = [getattr(w, "name", None) for w in rows]
    assert parent_task_name in names, (
        f"Expected workflow '{parent_task_name}' to be registered on the Hatchet "
        f"server, but only saw: {names}"
    )
    assert child_task_name in names, (
        f"Expected workflow '{child_task_name}' to be registered on the Hatchet "
        f"server, but only saw: {names}"
    )


def test_parent_workflow_run_succeeded(
    hatchet_client, logged_workflow_run_id: str
):
    """The recorded parent workflow run must exist on the server and have succeeded."""
    # Try the synchronous get; fall back to status-only lookup if get() unavailable.
    try:
        run = hatchet_client.runs.get(logged_workflow_run_id)
    except AttributeError:
        run = None

    if run is not None:
        status = (
            getattr(run, "status", None)
            or getattr(getattr(run, "run", None), "status", None)
        )
        assert _is_successful(status), (
            f"Expected parent run {logged_workflow_run_id} to have a successful "
            f"terminal status, but got: {status!r}"
        )
    else:
        status = hatchet_client.runs.get_status(logged_workflow_run_id)
        assert _is_successful(status), (
            f"Expected parent run {logged_workflow_run_id} status to be successful, "
            f"but got: {status!r}"
        )


def test_parent_workflow_run_total_is_55(
    hatchet_client, logged_workflow_run_id: str
):
    """When the run output is exposed via the SDK, the aggregated total must equal 55."""
    try:
        run = hatchet_client.runs.get(logged_workflow_run_id)
    except AttributeError:
        pytest.skip("hatchet_sdk runs client does not expose .get()")
        return

    # The output may be on run.output, run.tasks[*].output, or nested under run.run.
    output = (
        getattr(run, "output", None)
        or getattr(getattr(run, "run", None), "output", None)
    )

    # Some SDK versions expose tasks/run_output mappings; collect any "total" we can find.
    candidates = []
    if isinstance(output, dict):
        candidates.append(output)
    tasks = getattr(run, "tasks", None) or []
    for t in tasks:
        t_out = getattr(t, "output", None)
        if isinstance(t_out, dict):
            candidates.append(t_out)

    total_values = []
    for c in candidates:
        if "total" in c:
            total_values.append(c["total"])
        else:
            for v in c.values():
                if isinstance(v, dict) and "total" in v:
                    total_values.append(v["total"])

    if not total_values:
        pytest.skip(
            "SDK did not expose a parseable 'total' in run output; log-file "
            "verification already asserts Total: 55."
        )
        return

    assert any(int(v) == 55 for v in total_values), (
        f"Expected the parent run to return total=55, but observed totals: "
        f"{total_values}"
    )


def test_at_least_five_child_runs_were_spawned(
    hatchet_client, child_task_name: str
):
    """The child workflow must have at least 5 successful runs, proving real spawning."""
    workflows = hatchet_client.workflows.list()
    rows = getattr(workflows, "rows", None) or []
    child_workflow = next(
        (w for w in rows if getattr(w, "name", None) == child_task_name),
        None,
    )
    assert child_workflow is not None, (
        f"Child workflow '{child_task_name}' is not registered on the Hatchet "
        f"server."
    )

    child_workflow_id = getattr(
        getattr(child_workflow, "metadata", None), "id", None
    ) or getattr(child_workflow, "id", None)
    assert child_workflow_id, (
        f"Could not determine workflow ID for child workflow {child_task_name}."
    )

    runs = hatchet_client.runs.list(workflow_ids=[child_workflow_id])
    rows = getattr(runs, "rows", None) or []

    assert len(rows) >= 5, (
        f"Expected at least 5 child workflow runs for '{child_task_name}', "
        f"but found {len(rows)}. This suggests the parent did not actually "
        f"spawn child tasks via Hatchet."
    )

    successful = [r for r in rows if _is_successful(
        getattr(r, "status", None)
        or getattr(getattr(r, "run", None), "status", None)
    )]
    assert len(successful) >= 5, (
        f"Expected at least 5 successful child runs for '{child_task_name}', "
        f"but only {len(successful)} of {len(rows)} succeeded."
    )
