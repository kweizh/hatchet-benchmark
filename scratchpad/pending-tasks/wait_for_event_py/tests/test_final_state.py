import json
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/project"
ENV_FILE = Path("/etc/hatchet.env")


def _wait_for_hatchet_env(timeout: float = 180.0) -> None:
    """Block until the container bootstrap finishes and the API token is ready.

    Loads the persisted env vars from /etc/hatchet.env into os.environ so that
    child processes (the user worker + trigger) inherit them.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ENV_FILE.exists():
            try:
                text = ENV_FILE.read_text()
            except OSError:
                text = ""
            if "HATCHET_CLIENT_TOKEN=" in text and len(text.strip()) > 80:
                for line in text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    if key:
                        os.environ[key] = value
                return
        time.sleep(2)
    raise RuntimeError(
        "Container bootstrap (/etc/hatchet.env) did not become ready within "
        f"{timeout} seconds; cannot run the Hatchet wait-for-event test."
    )


@pytest.fixture(scope="session", autouse=True)
def _ensure_hatchet_bootstrap():
    _wait_for_hatchet_env()
    yield


@pytest.fixture(scope="session")
def hatchet_worker(xprocess):
    """Start the user's Hatchet worker in the background for the test session."""

    class Starter(ProcessStarter):
        name = "hatchet_worker"
        args = ["python", "-u", "worker.py"]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True
        # Match common Hatchet worker startup log lines (printed via stdlib/loguru/stdlib logger).
        pattern = r"(STARTING HATCHET|starting runner|listener|acquired action listener|registering worker|worker started|waiting for)"

    xprocess.ensure(Starter.name, Starter)

    # Give the gRPC registration a moment to settle before triggering.
    time.sleep(5)

    yield

    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_hatchet_grpc_reachable():
    """Sanity check: the local hatchet engine must accept connections on 7077."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        result = sock.connect_ex(("127.0.0.1", 7077))
    finally:
        sock.close()
    assert result == 0, (
        f"Expected local hatchet-lite gRPC port 7077 to be reachable; "
        f"connect_ex returned {result}."
    )


def test_user_project_files_exist():
    worker_py = os.path.join(PROJECT_DIR, "worker.py")
    trigger_py = os.path.join(PROJECT_DIR, "trigger.py")
    assert os.path.isfile(worker_py), f"Expected worker script at {worker_py}."
    assert os.path.isfile(trigger_py), f"Expected trigger script at {trigger_py}."


def test_trigger_pushes_event_and_durable_task_returns_payload(hatchet_worker):
    """Trigger the durable task, push the event, and verify the returned result."""
    env = os.environ.copy()

    result = subprocess.run(
        ["python", "-u", "trigger.py"],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
    )

    assert result.returncode == 0, (
        "trigger.py exited with non-zero status.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    # Locate the last non-empty stdout line and parse as JSON.
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    assert lines, (
        "trigger.py produced no stdout output. "
        f"stderr was:\n{result.stderr}"
    )

    parsed = None
    last_error: Exception | None = None
    for ln in reversed(lines):
        try:
            parsed = json.loads(ln)
            break
        except json.JSONDecodeError as exc:
            last_error = exc
            continue

    assert parsed is not None, (
        "Could not find a JSON object on trigger.py stdout. "
        f"stdout was:\n{result.stdout}\n"
        f"Last JSON error: {last_error}"
    )

    assert isinstance(parsed, dict), (
        f"Expected a JSON object from trigger.py, got: {type(parsed).__name__} ({parsed!r})"
    )
    assert parsed.get("status") == "completed", (
        f"Expected task result status == 'completed', got: {parsed!r}"
    )
    assert parsed.get("payload") == {"userId": "u1"}, (
        f"Expected task result payload == {{'userId': 'u1'}}, got: {parsed!r}"
    )
