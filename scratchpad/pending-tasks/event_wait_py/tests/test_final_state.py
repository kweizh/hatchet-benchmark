import json
import os
import pathlib

RESULT_PATH = "/tmp/result.json"
EVENTS_LOG_PATH = "/tmp/events.log"
PROJECT_DIR = "/home/user/myproject"


def test_result_file_exists():
    """The task runner must create /tmp/result.json after the durable task resolves."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected result file {RESULT_PATH} to exist after the task runs. "
        "The runner must invoke the Hatchet durable task and write its output to this path."
    )


def test_result_file_is_valid_json_object():
    with open(RESULT_PATH, "r") as f:
        raw = f.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{RESULT_PATH} is not valid JSON: {exc}. File contents (first 500 chars): {raw[:500]!r}"
        )
    assert isinstance(data, dict), (
        f"Expected {RESULT_PATH} to contain a JSON object (dict). Got type: {type(data).__name__}."
    )


def test_result_status_completed_via_event():
    with open(RESULT_PATH, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected JSON object in {RESULT_PATH}; got {type(data).__name__}."
    )
    assert "status" in data, (
        f"Expected top-level key 'status' in {RESULT_PATH}. Found keys: {sorted(data.keys())!r}"
    )
    expected = "completed_via_event"
    assert data["status"] == expected, (
        f"Expected status == {expected!r} in {RESULT_PATH}, got {data['status']!r}. "
        "This indicates the durable task resolved via the 30-second timeout rather than via the "
        "pushed 'user:profile_completed' event; the runner must push the event before the timeout."
    )


def test_events_log_contains_started_line():
    """The durable task body must have appended the started marker to /tmp/events.log."""
    assert os.path.isfile(EVENTS_LOG_PATH), (
        f"Expected events log {EVENTS_LOG_PATH} to exist after the durable task runs. "
        "The durable task's first action must append a line to this file."
    )
    with open(EVENTS_LOG_PATH, "r") as f:
        contents = f.read()
    assert "onboarding_flow started" in contents, (
        f"Expected {EVENTS_LOG_PATH} to contain the line 'onboarding_flow started' written from "
        f"inside the durable task body. Got contents (first 500 chars): {contents[:500]!r}."
    )


def test_runner_source_present_in_project_dir():
    """A Python source file must exist in the project directory, indicating the agent wrote real code."""
    project_path = pathlib.Path(PROJECT_DIR)
    assert project_path.is_dir(), (
        f"Expected project directory {PROJECT_DIR} to exist."
    )
    py_files = list(project_path.rglob("*.py"))
    assert py_files, (
        f"Expected at least one .py source file under {PROJECT_DIR} (the Hatchet durable task and runner). "
        "Found none."
    )
