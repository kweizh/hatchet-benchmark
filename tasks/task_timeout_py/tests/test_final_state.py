import json
import os
import subprocess

import pytest


PROJECT_DIR = "/home/user/myproject"
ENTRY = os.path.join(PROJECT_DIR, "main.py")
RESULT_FILE = "/tmp/result.json"


@pytest.fixture(scope="module")
def run_project():
    # Clean any prior result file so we verify a fresh run.
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)

    completed = subprocess.run(
        ["python3", ENTRY],
        cwd=PROJECT_DIR,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return completed


def test_runner_exits_cleanly(run_project):
    assert run_project.returncode == 0, (
        f"Runner exited with non-zero return code {run_project.returncode}. "
        f"stdout=\n{run_project.stdout}\nstderr=\n{run_project.stderr}"
    )


def test_result_file_exists(run_project):
    assert os.path.isfile(RESULT_FILE), (
        f"Expected result file {RESULT_FILE} to exist after running the project, but it does not."
    )


def test_result_indicates_timeout(run_project):
    with open(RESULT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f"{RESULT_FILE} is not valid JSON: {exc}")

    assert isinstance(data, dict), (
        f"Expected the contents of {RESULT_FILE} to be a JSON object, got: {type(data).__name__}"
    )
    assert "timed_out" in data, (
        f"Expected key 'timed_out' to be present in {RESULT_FILE}, got keys: {list(data.keys())}"
    )
    assert data["timed_out"] is True, (
        f"Expected 'timed_out' to be true in {RESULT_FILE}, got: {data!r}"
    )
