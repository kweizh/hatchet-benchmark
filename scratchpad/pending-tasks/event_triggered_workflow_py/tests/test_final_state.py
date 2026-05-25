import os
import re
import time

import pytest


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "welcome.log")

WELCOME_LINE_RE = re.compile(r"^Welcomed user\s+\S+@\S+\s*$", re.MULTILINE)


def _run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID env var must be set for verification."
    return rid


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to be created by the event-triggered task."
    )


def test_log_file_contains_welcome_line():
    with open(LOG_FILE, "r", encoding="utf-8") as fp:
        content = fp.read()
    assert WELCOME_LINE_RE.search(content), (
        f"Expected a line matching 'Welcomed user <email>' in {LOG_FILE}, got:\n{content!r}"
    )


@pytest.fixture(scope="session")
def hatchet_client():
    from hatchet_sdk import Hatchet  # imported lazily so other tests can run if SDK is missing

    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set for the verifier."
    assert server_url, "HATCHET_SERVER_URL must be set for the verifier."
    return Hatchet()


def _collect_run_records(hatchet_client):
    """Return a best-effort flat list of run records using whichever runs API is available."""
    runs_api = getattr(hatchet_client, "runs", None)
    assert runs_api is not None, "hatchet client does not expose a 'runs' API; cannot verify event trigger."

    list_fn = getattr(runs_api, "list", None)
    assert callable(list_fn), "hatchet.runs.list(...) is not available on this SDK build."

    last_err = None
    for kwargs in (
        {"limit": 50},
        {},
    ):
        try:
            result = list_fn(**kwargs)
            return result
        except TypeError as exc:
            last_err = exc
            continue
    raise AssertionError(f"Failed to call hatchet.runs.list(...): {last_err!r}")


def _records_iter(result):
    """Yield individual run records from heterogeneous SDK return shapes."""
    if result is None:
        return
    if isinstance(result, list):
        yield from result
        return
    for attr in ("rows", "runs", "items", "data", "results"):
        rows = getattr(result, attr, None)
        if rows:
            yield from rows
            return
    try:
        yield from iter(result)
    except TypeError:
        return


def _record_field(rec, *names, default=None):
    for n in names:
        if isinstance(rec, dict) and n in rec and rec[n] is not None:
            return rec[n]
        v = getattr(rec, n, None)
        if v is not None:
            return v
    return default


def test_run_visible_in_hatchet_for_event_key(hatchet_client):
    run_id = _run_id()
    expected_workflow_name = f"user-signup-handler-{run_id}"
    expected_event_key = f"user:signup:{run_id}"

    deadline = time.time() + 30
    match = None
    last_seen_workflow_names = set()

    while time.time() < deadline:
        result = _collect_run_records(hatchet_client)
        for rec in _records_iter(result):
            wf_name = _record_field(
                rec,
                "workflow_name",
                "workflowName",
                "workflow",
                default="",
            )
            if isinstance(wf_name, dict):
                wf_name = wf_name.get("name", "") or ""
            last_seen_workflow_names.add(str(wf_name))

            triggered_by = _record_field(
                rec,
                "triggering_event_key",
                "triggered_by",
                "trigger",
                "event_key",
                default=None,
            )
            if isinstance(triggered_by, dict):
                triggered_by_key = (
                    triggered_by.get("event_key")
                    or triggered_by.get("key")
                    or triggered_by.get("name")
                    or ""
                )
            else:
                triggered_by_key = str(triggered_by) if triggered_by else ""

            if (
                str(wf_name) == expected_workflow_name
                or expected_event_key in triggered_by_key
            ):
                match = rec
                break
        if match is not None:
            break
        time.sleep(2)

    assert match is not None, (
        f"Did not find a Hatchet run for workflow '{expected_workflow_name}' "
        f"triggered by event '{expected_event_key}'. "
        f"Seen workflow names (sample): {sorted(last_seen_workflow_names)[:20]}"
    )

    status = _record_field(match, "status", "state", default="")
    if isinstance(status, dict):
        status = status.get("status") or status.get("state") or ""
    status_str = str(status).upper()
    assert any(s in status_str for s in ("SUCCEED", "COMPLETED", "SUCCESS")), (
        f"Expected the event-triggered run to be in a successful terminal state, got status={status!r}"
    )
