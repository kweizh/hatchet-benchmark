import json
import os
import re

import pytest

LOG_PATH = "/home/user/myproject/output.log"


def _read_log():
    assert os.path.isfile(LOG_PATH), (
        f"Log file {LOG_PATH} does not exist. The task is expected to "
        f"write the workflow run results to this file."
    )
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_run_id(log_text):
    match = re.search(r"^Run ID:\s*(\S+)\s*$", log_text, re.MULTILINE)
    assert match, (
        "Log file must contain a line in the format 'Run ID: <workflow_run_id>'. "
        f"Got log contents:\n{log_text}"
    )
    run_id = match.group(1).strip()
    assert run_id, "Run ID line was found but the run id value is empty."
    return run_id


def _extract_output_json(log_text):
    match = re.search(r"^Output:\s*(\{.*\})\s*$", log_text, re.MULTILINE)
    assert match, (
        "Log file must contain a line in the format 'Output: <json_object>'. "
        f"Got log contents:\n{log_text}"
    )
    raw = match.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"The 'Output:' line must contain a valid JSON object. "
            f"Got: {raw!r}. JSON error: {e}"
        )


def test_log_file_exists():
    assert os.path.isfile(LOG_PATH), (
        f"Log file {LOG_PATH} does not exist."
    )


def test_log_contains_run_id():
    log_text = _read_log()
    _extract_run_id(log_text)


def test_log_contains_output_json():
    log_text = _read_log()
    payload = _extract_output_json(log_text)
    for field in ("start_ts", "end_ts", "duration_sec"):
        assert field in payload, (
            f"Output JSON must contain field '{field}'. Got: {payload}"
        )
        assert isinstance(payload[field], (int, float)), (
            f"Field '{field}' must be a number. Got: {payload[field]!r}"
        )


def test_duration_sec_at_least_5():
    log_text = _read_log()
    payload = _extract_output_json(log_text)
    duration = float(payload["duration_sec"])
    assert duration >= 5.0, (
        f"Durable sleep should have waited at least 5 seconds, but "
        f"duration_sec={duration}"
    )


def test_end_minus_start_at_least_5():
    log_text = _read_log()
    payload = _extract_output_json(log_text)
    start = float(payload["start_ts"])
    end = float(payload["end_ts"])
    assert (end - start) >= 5.0, (
        f"end_ts - start_ts should be >= 5.0 seconds, but got "
        f"start_ts={start}, end_ts={end}, diff={end - start}"
    )


def test_workflow_run_status_via_sdk():
    """Use Hatchet Python SDK to verify the workflow run finished successfully."""
    log_text = _read_log()
    run_id = _extract_run_id(log_text)
    zealt_run_id = os.environ.get("ZEALT_RUN_ID")
    assert zealt_run_id, "ZEALT_RUN_ID must be set in the verifier environment."

    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set in the verifier environment."
    assert server_url, "HATCHET_SERVER_URL must be set in the verifier environment."

    try:
        from hatchet_sdk import Hatchet
    except ImportError as e:
        pytest.fail(f"hatchet_sdk is not installed in the verifier environment: {e}")

    hatchet = Hatchet()

    # Try to fetch the run details using the REST client. The exact method
    # name has varied across hatchet-sdk versions, so try a couple of options.
    run = None
    last_err = None
    for getter in (
        lambda: hatchet.runs.get(run_id),
        lambda: hatchet.rest.workflow_run_get(run_id),
        lambda: hatchet.client.rest.workflow_run_get(run_id),
    ):
        try:
            run = getter()
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue

    assert run is not None, (
        f"Could not fetch workflow run {run_id} via the Hatchet SDK. "
        f"Last error: {last_err}"
    )

    # Status may live at different attribute paths depending on SDK version.
    status_candidates = []
    for attr_path in ("status", "run.status", "workflowRunStatus"):
        obj = run
        try:
            for part in attr_path.split("."):
                obj = getattr(obj, part)
            status_candidates.append(str(obj))
        except AttributeError:
            continue

    # Fallback: stringify the whole run object.
    blob = " ".join(status_candidates) if status_candidates else str(run)
    assert re.search(r"SUCCEED|COMPLETED|FINISHED|SUCCESS", blob, re.IGNORECASE), (
        f"Expected workflow run {run_id} to be in a successful state, but "
        f"got status info: {blob}"
    )

    # And the workflow name should be related to durable-sleep-${ZEALT_RUN_ID}.
    expected_name_fragment = f"durable-sleep-{zealt_run_id}"
    assert expected_name_fragment.lower() in str(run).lower(), (
        f"Expected the workflow run to be associated with a workflow named "
        f"'{expected_name_fragment}', but the run details did not reference it. "
        f"Run details: {run}"
    )
