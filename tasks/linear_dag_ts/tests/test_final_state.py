import json
import os
import signal
import socket
import subprocess
import time

import pytest

PROJECT_DIR = "/home/user/myproject"
RESULT_FILE = "/tmp/result.json"


def _wait_for_worker_ready(log_path: str, timeout: float = 60.0) -> bool:
    """Wait until the worker log indicates the worker is connected/listening."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.isfile(log_path):
            try:
                with open(log_path, "r") as f:
                    content = f.read().lower()
            except OSError:
                content = ""
            # Hatchet workers print a startup banner once registered.
            if (
                "starting hatchet" in content
                or "waiting for" in content
                or "listener" in content
                or "heartbeat" in content
            ):
                return True
        time.sleep(1.0)
    return False


@pytest.fixture(scope="session")
def run_workflow():
    """Start the Hatchet worker, trigger the workflow, then tear the worker down."""
    # Clean up any previous result.
    if os.path.isfile(RESULT_FILE):
        os.remove(RESULT_FILE)

    env = os.environ.copy()

    worker_log_path = "/tmp/worker.log"
    if os.path.isfile(worker_log_path):
        os.remove(worker_log_path)

    worker_log = open(worker_log_path, "w")
    worker_proc = subprocess.Popen(
        ["npm", "run", "worker"],
        cwd=PROJECT_DIR,
        env=env,
        stdout=worker_log,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )

    try:
        # Give the worker time to connect to Hatchet Cloud and register.
        _wait_for_worker_ready(worker_log_path, timeout=60.0)
        # Add a small extra buffer in case readiness detection was based on a partial log.
        time.sleep(5.0)

        # Trigger the workflow run (blocks until completion).
        run_result = subprocess.run(
            ["npm", "run", "run"],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        yield run_result
    finally:
        try:
            os.killpg(os.getpgid(worker_proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            worker_proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(worker_proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        worker_log.close()


def test_runner_succeeded(run_workflow):
    result = run_workflow
    assert result.returncode == 0, (
        f"Runner command 'npm run run' failed with code {result.returncode}.\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_result_file_exists(run_workflow):
    assert os.path.isfile(RESULT_FILE), (
        f"Expected result file {RESULT_FILE} to be created by the runner, but it was not."
    )


def test_result_file_contains_expected_final_value(run_workflow):
    with open(RESULT_FILE, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected {RESULT_FILE} to contain a JSON object, got {type(data).__name__}: {data!r}"
    )
    assert "final" in data, (
        f"Expected key 'final' in {RESULT_FILE}; got keys: {list(data.keys())}"
    )
    assert data["final"] == "hello world!", (
        f"Expected final == 'hello world!' in {RESULT_FILE}, got: {data['final']!r}"
    )
