import os
import re
import time

import pytest

LOG_FILE = "/home/user/myproject/output.log"


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _alpha_team() -> str:
    return f"alpha-{_run_id()}"


def _beta_team() -> str:
    return f"beta-{_run_id()}"


def _read_log() -> str:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _parse_run_lines(content: str):
    """Return list of (run_id, team) tuples from log lines matching the format
    `Run id=<workflow_run_id> team=<team_value>`.
    """
    pattern = re.compile(r"^Run id=(\S+) team=(\S+)\s*$", re.MULTILINE)
    return pattern.findall(content)


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the task completes."


def test_log_contains_three_run_lines_with_expected_team_distribution():
    content = _read_log()
    matches = _parse_run_lines(content)
    assert len(matches) == 3, (
        f"Expected exactly 3 `Run id=... team=...` lines in {LOG_FILE}, got {len(matches)}. "
        f"Log contents:\n{content}"
    )
    teams = [team for _run_id, team in matches]
    alpha_count = sum(1 for t in teams if t == _alpha_team())
    beta_count = sum(1 for t in teams if t == _beta_team())
    assert alpha_count == 2, (
        f"Expected exactly 2 run lines with team={_alpha_team()}, got {alpha_count}. Teams seen: {teams}"
    )
    assert beta_count == 1, (
        f"Expected exactly 1 run line with team={_beta_team()}, got {beta_count}. Teams seen: {teams}"
    )


def test_log_contains_alpha_run_count_line():
    content = _read_log()
    expected = "Alpha run count: 2"
    assert expected in content, (
        f"Expected log file {LOG_FILE} to contain the final line '{expected}', "
        f"but it was not found. Log contents:\n{content}"
    )


def _list_runs_by_metadata(hatchet, metadata: dict):
    """Call hatchet.runs.list with retries to allow Hatchet to finalize state."""
    deadline = time.time() + 120
    last_err = None
    while time.time() < deadline:
        try:
            return hatchet.runs.list(additional_metadata=metadata)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2)
    raise AssertionError(f"Failed to list runs with metadata={metadata}: {last_err}")


def _get_run_metadata(run) -> dict:
    """Extract the additional_metadata dict from a V1TaskSummary-style row."""
    md = getattr(run, "additional_metadata", None)
    if md is None:
        md = getattr(run, "additionalMetadata", None)
    if md is None:
        return {}
    if isinstance(md, dict):
        return md
    if hasattr(md, "to_dict"):
        try:
            d = md.to_dict()
            if isinstance(d, dict):
                return d
        except Exception:  # noqa: BLE001
            pass
    if hasattr(md, "__dict__"):
        return {k: v for k, v in md.__dict__.items() if not k.startswith("_")}
    return {}


def _get_run_id_value(run):
    md = getattr(run, "metadata", None)
    rid = getattr(md, "id", None) if md is not None else None
    if not rid:
        rid = getattr(run, "id", None)
    if not rid:
        rid = getattr(run, "external_id", None)
    if not rid:
        rid = getattr(run, "externalId", None)
    return rid


def _get_run_status(run) -> str:
    status = getattr(run, "status", None)
    return str(getattr(status, "value", status)).upper() if status is not None else ""


def test_hatchet_alpha_runs_match_metadata_filter():
    """Query the Hatchet server and verify exactly 2 runs match team=alpha-${run-id}."""
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."

    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    runs = _list_runs_by_metadata(hatchet, {"team": _alpha_team()})
    rows = getattr(runs, "rows", None) or []

    # Scope down to runs that belong to this trial (other concurrent trials may pollute the tenant).
    own_rows = [r for r in rows if _get_run_metadata(r).get("zealt_run_id") == _run_id()]
    assert len(own_rows) == 2, (
        f"Expected exactly 2 Hatchet runs tagged team={_alpha_team()} for this trial, "
        f"but found {len(own_rows)}. Raw rows: {rows}"
    )
    for run in own_rows:
        md = _get_run_metadata(run)
        assert md.get("team") == _alpha_team(), (
            f"Expected run additional_metadata team={_alpha_team()}, got {md.get('team')!r}. Full metadata: {md}"
        )


def test_hatchet_beta_runs_match_metadata_filter():
    """Query the Hatchet server and verify exactly 1 run matches team=beta-${run-id}."""
    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    runs = _list_runs_by_metadata(hatchet, {"team": _beta_team()})
    rows = getattr(runs, "rows", None) or []
    own_rows = [r for r in rows if _get_run_metadata(r).get("zealt_run_id") == _run_id()]
    assert len(own_rows) == 1, (
        f"Expected exactly 1 Hatchet run tagged team={_beta_team()} for this trial, "
        f"but found {len(own_rows)}. Raw rows: {rows}"
    )
    md = _get_run_metadata(own_rows[0])
    assert md.get("team") == _beta_team(), (
        f"Expected run additional_metadata team={_beta_team()}, got {md.get('team')!r}. Full metadata: {md}"
    )


def test_log_run_ids_are_present_on_server_and_succeeded():
    """The three workflow_run_ids logged by the task must all be present in the
    union of the alpha and beta query results, and each must be in a terminal
    success state.
    """
    content = _read_log()
    matches = _parse_run_lines(content)
    assert len(matches) == 3, f"Expected 3 logged runs, found {len(matches)}."
    logged_ids = {rid for rid, _team in matches}

    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    alpha_runs = _list_runs_by_metadata(hatchet, {"team": _alpha_team()})
    beta_runs = _list_runs_by_metadata(hatchet, {"team": _beta_team()})

    combined = []
    combined.extend(getattr(alpha_runs, "rows", None) or [])
    combined.extend(getattr(beta_runs, "rows", None) or [])

    server_by_id = {}
    for run in combined:
        rid = _get_run_id_value(run)
        if rid is None:
            continue
        server_by_id[str(rid)] = run

    missing = [rid for rid in logged_ids if rid not in server_by_id]
    assert not missing, (
        f"The following workflow_run_ids logged by the task were not found on the Hatchet server "
        f"under the expected team metadata filters: {missing}. "
        f"Server-known ids for this trial: {list(server_by_id.keys())}"
    )

    terminal_success_statuses = {"COMPLETED", "SUCCEEDED", "SUCCESS"}
    for rid in logged_ids:
        run = server_by_id[rid]
        status = _get_run_status(run)
        assert status in terminal_success_statuses, (
            f"Expected run {rid} to be in a terminal success state "
            f"(one of {sorted(terminal_success_statuses)}), got status={status!r}."
        )
