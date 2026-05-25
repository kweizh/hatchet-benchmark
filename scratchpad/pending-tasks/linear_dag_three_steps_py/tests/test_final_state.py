import os
import re
import time

import pytest

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
RUN_ID_PATTERN = re.compile(r"^Workflow Run ID:\s*([0-9a-fA-F-]+)\s*$", re.MULTILINE)


def _read_run_id_from_log():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE) as f:
        content = f.read()
    matches = RUN_ID_PATTERN.findall(content)
    assert matches, (
        f"Log file {LOG_FILE} does not contain a line matching "
        f"'Workflow Run ID: <run_id>'. Got:\n{content}"
    )
    return matches[-1].strip()


def _get_hatchet_client():
    from hatchet_sdk import Hatchet

    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set for verification."
    assert server_url, "HATCHET_SERVER_URL must be set for verification."
    return Hatchet()


def _wait_for_run_terminal(hatchet, run_id, timeout=120):
    deadline = time.time() + timeout
    last_status = None
    while time.time() < deadline:
        try:
            status = hatchet.runs.get_status(run_id)
        except Exception as exc:  # noqa: BLE001
            last_status = f"error: {exc}"
            time.sleep(2)
            continue
        last_status = status
        status_str = str(status).upper()
        if any(s in status_str for s in ("SUCCEEDED", "COMPLETED", "FAILED", "CANCELLED")):
            return status_str
        time.sleep(2)
    raise AssertionError(
        f"Workflow run {run_id} did not reach a terminal status within {timeout}s; "
        f"last observed status: {last_status}"
    )


def test_log_file_contains_workflow_run_id():
    run_id = _read_run_id_from_log()
    assert re.fullmatch(r"[0-9a-fA-F-]+", run_id), (
        f"Captured run ID '{run_id}' does not look like a valid Hatchet run ID."
    )


def test_workflow_run_succeeded():
    run_id = _read_run_id_from_log()
    hatchet = _get_hatchet_client()
    status_str = _wait_for_run_terminal(hatchet, run_id, timeout=120)
    assert "SUCCEEDED" in status_str or "COMPLETED" in status_str, (
        f"Workflow run {run_id} did not succeed. Final status: {status_str}"
    )


def test_workflow_name_includes_run_id_suffix():
    run_id = _read_run_id_from_log()
    zealt_run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert zealt_run_id, "ZEALT_RUN_ID environment variable must be set for verification."

    hatchet = _get_hatchet_client()
    _wait_for_run_terminal(hatchet, run_id, timeout=120)

    details = hatchet.runs.get(run_id)
    expected_name = f"greeting-pipeline-{zealt_run_id}"
    name_str = ""
    # Try multiple possible attribute paths to be robust to SDK shape differences.
    for path in ("run.display_name", "run.workflow_name", "workflow_name", "display_name"):
        obj = details
        ok = True
        for part in path.split("."):
            if obj is None:
                ok = False
                break
            obj = getattr(obj, part, None)
        if ok and isinstance(obj, str) and obj:
            name_str = obj
            if expected_name in name_str:
                break

    assert expected_name in (name_str or repr(details)), (
        f"Expected workflow name to contain '{expected_name}', "
        f"but got: {name_str!r} (details repr: {details!r})"
    )


def test_step_outputs_match_expected_transformations():
    run_id = _read_run_id_from_log()
    hatchet = _get_hatchet_client()
    _wait_for_run_terminal(hatchet, run_id, timeout=120)

    result = hatchet.runs.get_result(run_id)
    assert result is not None, f"hatchet.runs.get_result({run_id}) returned None."

    # `get_result` returns a JSON-serializable mapping. Depending on SDK version,
    # outputs may be keyed by short task name (e.g., "step1") or by a fully
    # qualified name. Flatten the structure so we can find each step's output.
    def _walk(obj, out):
        if isinstance(obj, dict):
            for k, v in obj.items():
                out.setdefault(k, v)
                if isinstance(v, dict):
                    _walk(v, out)
        return out

    flat = _walk(dict(result), {})

    def _find_step_output(step_name):
        for key, value in flat.items():
            if isinstance(value, dict) and key.split(":")[-1].split(".")[-1] == step_name:
                return value
        # Fallback: substring match on key.
        for key, value in flat.items():
            if isinstance(value, dict) and step_name in key:
                return value
        return None

    step1_out = _find_step_output("step1")
    step2_out = _find_step_output("step2")
    step3_out = _find_step_output("step3")

    assert step1_out is not None, (
        f"Could not find step1 output in workflow result keys: {list(flat.keys())}"
    )
    assert step2_out is not None, (
        f"Could not find step2 output in workflow result keys: {list(flat.keys())}"
    )
    assert step3_out is not None, (
        f"Could not find step3 output in workflow result keys: {list(flat.keys())}"
    )

    assert step1_out.get("greeting") == "Hello world", (
        f"step1 output expected greeting='Hello world', got: {step1_out}"
    )
    assert step2_out.get("shouted") == "HELLO WORLD", (
        f"step2 output expected shouted='HELLO WORLD', got: {step2_out}"
    )
    assert step3_out.get("final") == "HELLO WORLD!!!", (
        f"step3 output expected final='HELLO WORLD!!!', got: {step3_out}"
    )
