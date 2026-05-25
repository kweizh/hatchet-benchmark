import json
import os
import pathlib

RESULT_PATH = "/tmp/result.json"
PROJECT_DIR = "/home/user/myproject"


def test_result_file_exists():
    """The task runner must create /tmp/result.json after executing the task on Hatchet Cloud."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected result file {RESULT_PATH} to exist after the task runs. "
        "The runner must invoke the Hatchet task and write its output to this path."
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


def test_result_greeting_matches_expected():
    with open(RESULT_PATH, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected JSON object in {RESULT_PATH}; got {type(data).__name__}."
    )
    assert "greeting" in data, (
        f"Expected top-level key 'greeting' in {RESULT_PATH}. Found keys: {sorted(data.keys())!r}"
    )
    expected = "Hello, World!"
    assert data["greeting"] == expected, (
        f"Expected greeting == {expected!r} in {RESULT_PATH}, got {data['greeting']!r}."
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
