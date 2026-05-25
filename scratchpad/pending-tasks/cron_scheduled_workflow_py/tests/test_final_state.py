import os
import re
import time

import pytest

LOG_FILE = "/home/user/myproject/output.log"


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _task_name() -> str:
    return f"heartbeat-task-{_run_id()}"


def _cron_name() -> str:
    return f"heartbeat-cron-{_run_id()}"


# ---------------------------------------------------------------------------
# Shared module-level state so the cleanup test can delete the cron created by
# the task even if earlier assertions fail. pytest still runs the cleanup
# function, and pytest's default test order matches definition order.
# ---------------------------------------------------------------------------

_CREATED_CRON_IDS: list[str] = []


def _record_cron_id(cron_id: str | None) -> None:
    if cron_id and cron_id not in _CREATED_CRON_IDS:
        _CREATED_CRON_IDS.append(cron_id)


def _hatchet_client():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."

    from hatchet_sdk import Hatchet

    return Hatchet()


def _get_attr(obj, *names):
    """Return the first attribute (or dict key) found on ``obj``."""
    for name in names:
        if obj is None:
            return None
        val = getattr(obj, name, None)
        if val is not None:
            return val
        if isinstance(obj, dict) and name in obj:
            return obj[name]
    return None


# ---------------------------------------------------------------------------
# 1. Log file checks
# ---------------------------------------------------------------------------

def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task completes."
    )


def test_log_file_contains_cron_acknowledgement():
    """The log must contain a line like:
       `Created cron heartbeat-cron-<run-id> id=<cron_trigger_id>`."""
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    cron_name = _cron_name()
    pattern = re.compile(
        rf"Created cron\s+{re.escape(cron_name)}\s+id=(\S+)"
    )
    match = pattern.search(content)
    assert match, (
        f"Expected log file {LOG_FILE} to contain a line in the format "
        f"'Created cron {cron_name} id=<cron_trigger_id>'. Log contents:\n{content}"
    )

    cron_id = match.group(1).strip()
    assert cron_id, (
        f"Expected a non-empty cron_trigger_id in the log line for cron '{cron_name}'."
    )
    _record_cron_id(cron_id)


# ---------------------------------------------------------------------------
# 2. Hatchet server checks via the Python SDK
# ---------------------------------------------------------------------------

def test_hatchet_cron_schedule_exists():
    """Verify the cron schedule was created on the real Hatchet server with
    the expected name and `* * * * *` expression."""
    hatchet = _hatchet_client()
    cron_name = _cron_name()

    crons = None
    try:
        crons = hatchet.cron.list(cron_name=cron_name)
    except TypeError:
        # Older SDK signatures may not accept `cron_name`; fall back to
        # listing all crons and filtering in Python.
        crons = hatchet.cron.list()

    rows = _get_attr(crons, "rows") or []
    matching = []
    for row in rows:
        name = _get_attr(row, "cron_name", "name")
        if name == cron_name:
            matching.append(row)

    assert matching, (
        f"No Hatchet cron schedule named '{cron_name}' was found on the server. "
        f"Cron names available: {[_get_attr(r, 'cron_name', 'name') for r in rows]}"
    )

    cron = matching[0]
    expression = _get_attr(cron, "cron", "expression")
    assert expression == "* * * * *", (
        f"Expected cron '{cron_name}' to have expression '* * * * *', got {expression!r}."
    )

    # Record id for later cleanup.
    metadata = _get_attr(cron, "metadata")
    cron_id = _get_attr(metadata, "id") if metadata is not None else _get_attr(cron, "id")
    _record_cron_id(cron_id)


def test_hatchet_cron_triggered_at_least_one_run():
    """Wait up to ~80 seconds for the cron to fire at least once."""
    hatchet = _hatchet_client()
    task_name = _task_name()

    # 1. Look up the workflow id for the task.
    workflow_id: str | None = None
    deadline = time.time() + 30
    last_err: Exception | None = None
    while time.time() < deadline and workflow_id is None:
        try:
            workflows = hatchet.workflows.list()
            rows = _get_attr(workflows, "rows") or []
            for w in rows:
                if _get_attr(w, "name") == task_name:
                    metadata = _get_attr(w, "metadata")
                    workflow_id = (
                        _get_attr(metadata, "id") if metadata is not None
                        else _get_attr(w, "id")
                    )
                    if workflow_id:
                        break
        except Exception as e:  # noqa: BLE001
            last_err = e
        if workflow_id is None:
            time.sleep(2)

    assert workflow_id, (
        f"Could not find a Hatchet workflow named '{task_name}' on the server "
        f"(last error: {last_err})."
    )

    # 2. Poll the runs list until at least one run is recorded.
    deadline = time.time() + 80
    last_runs = None
    while time.time() < deadline:
        try:
            runs = hatchet.runs.list(workflow_ids=[workflow_id])
            run_rows = _get_attr(runs, "rows") or []
            last_runs = run_rows
            if run_rows:
                return
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(5)

    pytest.fail(
        f"Expected at least one cron-triggered run for workflow '{task_name}' "
        f"(workflow_id={workflow_id}) within ~80 seconds, but found "
        f"{0 if last_runs is None else len(last_runs)} runs. last_err={last_err}"
    )


# ---------------------------------------------------------------------------
# 3. Cleanup: delete the cron schedule from the Hatchet server.
# ---------------------------------------------------------------------------

def test_zzz_cleanup_delete_cron_schedule():
    """Best-effort cleanup so the per-minute cron does not accumulate runs on
    the shared Hatchet server. Runs last (alphabetical ordering)."""
    if not _CREATED_CRON_IDS:
        # Try to discover the cron one more time so we still clean up even if
        # earlier assertions skipped recording the id.
        try:
            hatchet = _hatchet_client()
            crons = hatchet.cron.list()
            rows = _get_attr(crons, "rows") or []
            for row in rows:
                name = _get_attr(row, "cron_name", "name")
                if name == _cron_name():
                    metadata = _get_attr(row, "metadata")
                    cron_id = (
                        _get_attr(metadata, "id") if metadata is not None
                        else _get_attr(row, "id")
                    )
                    _record_cron_id(cron_id)
        except Exception:  # noqa: BLE001
            pass

    if not _CREATED_CRON_IDS:
        pytest.skip("No cron id was recorded; nothing to clean up.")

    hatchet = _hatchet_client()
    errors: list[str] = []
    for cron_id in list(_CREATED_CRON_IDS):
        try:
            hatchet.cron.delete(cron_id=cron_id)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{cron_id}: {e}")

    # Cleanup failures should not mask earlier verification successes, but they
    # are still surfaced so operators can clean up manually if needed.
    assert not errors, f"Failed to delete cron schedule(s): {errors}"
