import os
import re

import pytest

LOG_FILE = "/home/user/myproject/output.log"

LINE_RE = re.compile(
    r"^amount=(?P<amount>50|500)\s+decision=(?P<decision>approved|auto)\s+run_id=(?P<run_id>\S+)$"
)


def _read_lines():
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh if line.strip()]


def _hatchet_client():
    from hatchet_sdk import Hatchet  # type: ignore

    return Hatchet()


@pytest.fixture(scope="module")
def parsed_lines():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    lines = _read_lines()
    assert len(lines) == 2, (
        f"Expected exactly 2 non-empty lines in {LOG_FILE}, got {len(lines)}: "
        f"{lines!r}"
    )
    parsed = []
    for line in lines:
        match = LINE_RE.match(line)
        assert match, (
            f"Log line does not match required format "
            f"'amount=<int> decision=<approved|auto> run_id=<id>': {line!r}"
        )
        parsed.append(match.groupdict())
    return parsed


@pytest.fixture(scope="module")
def by_amount(parsed_lines):
    by = {}
    for entry in parsed_lines:
        by.setdefault(entry["amount"], []).append(entry)
    assert "50" in by and len(by["50"]) == 1, (
        f"Expected exactly one log line with amount=50, got {by.get('50')}"
    )
    assert "500" in by and len(by["500"]) == 1, (
        f"Expected exactly one log line with amount=500, got {by.get('500')}"
    )
    return {"50": by["50"][0], "500": by["500"][0]}


@pytest.fixture(scope="module")
def expected_workflow_name():
    run_id_env = os.environ.get("ZEALT_RUN_ID")
    assert run_id_env, "ZEALT_RUN_ID env var must be set for verification."
    return f"approval-flow-{run_id_env}"


def _result_dict(result):
    """Normalize hatchet.runs.get_result(...) to a plain dict task_name -> output."""
    if result is None:
        return {}
    if hasattr(result, "model_dump"):
        try:
            return result.model_dump()
        except Exception:
            pass
    if hasattr(result, "dict"):
        try:
            return result.dict()
        except Exception:
            pass
    if isinstance(result, dict):
        return result
    raise AssertionError(
        f"Unexpected return type from hatchet.runs.get_result: {type(result)!r}"
    )


def _task_output(result_dict, task_name):
    """Look up a task's output in a result dict, tolerating various key shapes."""
    if not isinstance(result_dict, dict):
        return None
    if task_name in result_dict:
        return result_dict[task_name]
    for key, value in result_dict.items():
        if isinstance(key, str) and key.lower().endswith(task_name.lower()):
            return value
    return None


def test_log_line_for_amount_50_is_auto(by_amount):
    entry = by_amount["50"]
    assert entry["decision"] == "auto", (
        f"Expected decision=auto for amount=50, got decision={entry['decision']!r}"
    )


def test_log_line_for_amount_500_is_approved(by_amount):
    entry = by_amount["500"]
    assert entry["decision"] == "approved", (
        f"Expected decision=approved for amount=500, got decision={entry['decision']!r}"
    )


def test_amount_50_run_executed_auto_path(by_amount, expected_workflow_name):
    run_id = by_amount["50"]["run_id"]
    client = _hatchet_client()
    raw_result = client.runs.get_result(run_id)
    result = _result_dict(raw_result)
    auto = _task_output(result, "auto_path")
    assert auto is not None, (
        f"Expected the auto_path task to have produced an output in run "
        f"{run_id}; full result: {result!r}"
    )
    auto_val = None
    if isinstance(auto, dict):
        auto_val = auto.get("auto")
    assert auto_val is True, (
        f"Expected auto_path output to contain 'auto': True for run {run_id}, "
        f"got {auto!r}"
    )
    approve = _task_output(result, "approve_path")
    assert approve in (None, {}, [], False), (
        f"Expected approve_path to be skipped (no output) for run {run_id}, "
        f"got {approve!r}"
    )


def test_amount_500_run_executed_approve_path(by_amount, expected_workflow_name):
    run_id = by_amount["500"]["run_id"]
    client = _hatchet_client()
    raw_result = client.runs.get_result(run_id)
    result = _result_dict(raw_result)
    approve = _task_output(result, "approve_path")
    assert approve is not None, (
        f"Expected the approve_path task to have produced an output in run "
        f"{run_id}; full result: {result!r}"
    )
    approved_val = None
    if isinstance(approve, dict):
        approved_val = approve.get("approved")
    assert approved_val is True, (
        f"Expected approve_path output to contain 'approved': True for run "
        f"{run_id}, got {approve!r}"
    )
    auto = _task_output(result, "auto_path")
    assert auto in (None, {}, [], False), (
        f"Expected auto_path to be skipped (no output) for run {run_id}, "
        f"got {auto!r}"
    )


def test_runs_belong_to_expected_workflow(by_amount, expected_workflow_name):
    client = _hatchet_client()
    for entry in (by_amount["50"], by_amount["500"]):
        run_id = entry["run_id"]
        try:
            details = client.runs.get(run_id)
        except Exception as exc:
            raise AssertionError(
                f"hatchet.runs.get({run_id!r}) failed: {exc}"
            )
        details_dict = _result_dict(details)
        name_candidates = []
        for key in (
            "workflow_name",
            "workflowName",
            "workflow",
            "name",
        ):
            value = details_dict.get(key)
            if isinstance(value, str):
                name_candidates.append(value)
            elif isinstance(value, dict):
                inner = value.get("name") or value.get("workflow_name")
                if isinstance(inner, str):
                    name_candidates.append(inner)
        joined = " ".join(name_candidates)
        assert expected_workflow_name in joined, (
            f"Run {run_id} is not associated with the expected workflow "
            f"{expected_workflow_name!r}; got workflow name candidates: "
            f"{name_candidates!r}"
        )
