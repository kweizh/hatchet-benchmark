import json
import os
import re
import subprocess
import sys
import time

import pytest


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
MAIN_SCRIPT = os.path.join(PROJECT_DIR, "main.py")

PROCESS_TIMEOUT_SECONDS = 90
EVENT_PUSH_DELAY_SECONDS = 2.0


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID must be set in the verifier environment."
    return run_id


@pytest.fixture(scope="session")
def event_key() -> str:
    return f"user:profile-completed:{_run_id()}"


@pytest.fixture(scope="session")
def run_and_collect(event_key):
    """Run the agent's task script once, push the event ~2s in, capture the log."""
    assert os.path.isfile(MAIN_SCRIPT), (
        f"Expected the agent to create the main entry script at {MAIN_SCRIPT}."
    )

    # Ensure a clean log before each run.
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    env = os.environ.copy()
    # Sanity: required by both task and verifier.
    assert env.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN must be set in the verifier environment."
    )
    assert env.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL must be set in the verifier environment."
    )

    proc = subprocess.Popen(
        [sys.executable, MAIN_SCRIPT],
        cwd=PROJECT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Give the worker/run a moment to register, then push the event.
    push_error = None
    try:
        time.sleep(EVENT_PUSH_DELAY_SECONDS)
        try:
            from hatchet_sdk import Hatchet  # type: ignore
            hatchet = Hatchet()
            hatchet.event.push(event_key, {"userId": "test"})
        except Exception as exc:  # pragma: no cover - reported via assertion below
            push_error = exc

        try:
            stdout, _ = proc.communicate(timeout=PROCESS_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate()
            pytest.fail(
                "Task process did not exit within "
                f"{PROCESS_TIMEOUT_SECONDS}s. Captured output:\n{stdout}"
            )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)

    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "push_error": push_error,
    }


@pytest.fixture(scope="session")
def log_text(run_and_collect):
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task run. "
        f"Process stdout was:\n{run_and_collect['stdout']}"
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return fh.read()


def test_event_push_succeeded(run_and_collect):
    assert run_and_collect["push_error"] is None, (
        "Verifier failed to push the user:profile-completed event using the Hatchet SDK: "
        f"{run_and_collect['push_error']!r}"
    )


def test_task_process_exited_cleanly(run_and_collect):
    assert run_and_collect["returncode"] == 0, (
        "Task process did not exit cleanly. "
        f"returncode={run_and_collect['returncode']}, stdout=\n{run_and_collect['stdout']}"
    )


def test_log_contains_waiting_message(log_text):
    expected = "Waiting for user-profile-completed event or 30 second timeout"
    assert expected in log_text, (
        f"Expected the durable task to log the startup line {expected!r} but it was "
        f"missing from {LOG_FILE}. Log contents:\n{log_text}"
    )


def test_log_contains_run_result_line(log_text):
    matches = re.findall(r"^Run result: (.+)$", log_text, flags=re.MULTILINE)
    assert len(matches) >= 1, (
        f"Expected exactly one line starting with 'Run result: ' in {LOG_FILE}, "
        f"got {len(matches)}. Log contents:\n{log_text}"
    )


def test_run_result_indicates_event_received(log_text):
    match = re.search(r"^Run result: (.+)$", log_text, flags=re.MULTILINE)
    assert match, (
        f"Could not find a 'Run result: <json>' line in {LOG_FILE}. "
        f"Log contents:\n{log_text}"
    )
    raw = match.group(1).strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Run result line is not valid JSON: {raw!r} ({exc})"
        )
    assert isinstance(result, dict), (
        f"Expected the Run result JSON to be an object, got: {result!r}"
    )
    assert result.get("received_event") is True, (
        "Expected received_event=true after the verifier pushed the event, "
        f"but got: {result!r}"
    )
    payload = result.get("payload")
    assert isinstance(payload, dict), (
        f"Expected payload to be a JSON object, got: {payload!r}"
    )
    assert payload.get("userId") == "test", (
        f"Expected payload.userId == 'test' (the value pushed by the verifier), got: {payload!r}"
    )
