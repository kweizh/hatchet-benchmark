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


def _run_id() -> str:
    return os.environ.get("ZEALT_RUN_ID", "local") or "local"


def _counter_file_path() -> str:
    return f"/tmp/flaky-counter-{_run_id()}.txt"


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
        f"{timeout} seconds; cannot run the Hatchet retries test."
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


def test_trigger_runs_and_task_succeeds_after_three_attempts(hatchet_worker):
    """Trigger the workflow against the real Hatchet server and verify behavior."""
    counter_file = _counter_file_path()
    # Ensure a clean per-trial counter file.
    if os.path.exists(counter_file):
        os.remove(counter_file)

    env = os.environ.copy()

    result = subprocess.run(
        ["python", "-u", "trigger.py", counter_file],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
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
    assert parsed.get("attempt") == 3, (
        f"Expected task result attempt == 3, got: {parsed!r}"
    )
    assert parsed.get("succeeded") is True, (
        f"Expected task result succeeded == true, got: {parsed!r}"
    )

    # The counter file should now hold exactly 3 (initial attempt + 2 retries).
    assert os.path.isfile(counter_file), (
        f"Expected counter file {counter_file} to exist after the task succeeded."
    )
    with open(counter_file, "r", encoding="utf-8") as fh:
        raw = fh.read().strip()
    try:
        counter_value = int(raw)
    except ValueError:
        pytest.fail(
            f"Counter file {counter_file} did not contain an integer; got: {raw!r}"
        )
    assert counter_value == 3, (
        f"Expected counter file {counter_file} to contain 3 (initial + 2 retries), "
        f"got {counter_value}."
    )
