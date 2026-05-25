import json
import os
import pathlib

ATTEMPTS_PATH = "/tmp/attempts.txt"
RESULT_PATH = "/tmp/result.json"
PROJECT_DIR = "/home/user/myproject"


def test_attempts_file_exists():
    """The runner must produce /tmp/attempts.txt as the task body persists the attempt counter."""
    assert os.path.isfile(ATTEMPTS_PATH), (
        f"Expected attempts counter file {ATTEMPTS_PATH} to exist after the task runs. "
        "The flaky_task body must persist its attempt counter to this path."
    )


def test_attempts_value_is_three():
    with open(ATTEMPTS_PATH, "r") as f:
        raw = f.read()
    stripped = raw.strip()
    try:
        attempts = int(stripped)
    except ValueError as exc:
        raise AssertionError(
            f"{ATTEMPTS_PATH} does not contain a valid integer. File contents: {raw!r}. Error: {exc}"
        )
    assert attempts == 3, (
        f"Expected exactly 3 attempts (initial run + 2 retries before success) recorded in "
        f"{ATTEMPTS_PATH}, got {attempts}. The task is configured with retries=3 and must "
        "succeed on the third attempt."
    )


def test_result_file_exists():
    """The task runner must create /tmp/result.json after Hatchet returns the successful run output."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected result file {RESULT_PATH} to exist after the task runs. "
        "The runner must invoke the Hatchet task with retries and write its final output to this path."
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


def test_result_status_is_success():
    with open(RESULT_PATH, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected JSON object in {RESULT_PATH}; got {type(data).__name__}."
    )
    assert "status" in data, (
        f"Expected top-level key 'status' in {RESULT_PATH}. Found keys: {sorted(data.keys())!r}"
    )
    assert data["status"] == "success", (
        f"Expected status == 'success' in {RESULT_PATH}, got {data['status']!r}."
    )


def test_result_attempt_is_three():
    with open(RESULT_PATH, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected JSON object in {RESULT_PATH}; got {type(data).__name__}."
    )
    assert "attempt" in data, (
        f"Expected top-level key 'attempt' in {RESULT_PATH}. Found keys: {sorted(data.keys())!r}"
    )
    attempt_value = data["attempt"]
    assert isinstance(attempt_value, int) and not isinstance(attempt_value, bool), (
        f"Expected integer value for 'attempt' in {RESULT_PATH}; got type "
        f"{type(attempt_value).__name__} with value {attempt_value!r}."
    )
    assert attempt_value == 3, (
        f"Expected attempt == 3 in {RESULT_PATH}, got {attempt_value!r}. "
        "The task is configured with retries=3 and must succeed on the third attempt."
    )


def test_runner_source_present_in_project_dir():
    """A Python source file must exist in the project directory, indicating the agent wrote real code."""
    project_path = pathlib.Path(PROJECT_DIR)
    assert project_path.is_dir(), (
        f"Expected project directory {PROJECT_DIR} to exist."
    )
    py_files = list(project_path.rglob("*.py"))
    assert py_files, (
        f"Expected at least one .py source file under {PROJECT_DIR} (the Hatchet task and runner). "
        "Found none."
    )
