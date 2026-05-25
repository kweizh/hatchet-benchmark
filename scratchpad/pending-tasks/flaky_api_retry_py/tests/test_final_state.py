import json
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/project"
ENV_FILE = Path("/etc/hatchet.env")
COUNTER_FILE = Path("/var/lib/flaky/counter.txt")
FLAKY_HOST = "127.0.0.1"
FLAKY_PORT = 9001
HATCHET_GRPC_PORT = 7077

# Lower bound for the wall-clock duration of trigger.py. With retries=5 and
# backoff_factor=2.0, the minimum cumulative backoff before the 4th attempt
# succeeds is 2s + 4s + 8s = 14s, so 3s is a very conservative floor that
# still proves the backoff slept between retries.
MIN_DURATION_SEC = 3.0


def _wait_for_hatchet_env(timeout: float = 180.0) -> None:
    """Block until the container bootstrap finishes and the API token is ready."""
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
        f"{timeout} seconds; cannot run the Hatchet flaky-API retry test."
    )


def _reset_counter_file() -> None:
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    COUNTER_FILE.write_text("0")
    try:
        os.chmod(COUNTER_FILE, 0o666)
    except PermissionError:
        # Already writable by the verifier user.
        pass


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
        result = sock.connect_ex(("127.0.0.1", HATCHET_GRPC_PORT))
    finally:
        sock.close()
    assert result == 0, (
        f"Expected local hatchet-lite gRPC port {HATCHET_GRPC_PORT} to be reachable; "
        f"connect_ex returned {result}."
    )


def test_flaky_api_healthz_returns_200():
    """The local flaky API must be running on 127.0.0.1:9001 before the test."""
    deadline = time.time() + 30
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            resp = requests.get(f"http://{FLAKY_HOST}:{FLAKY_PORT}/healthz", timeout=5)
            assert resp.status_code == 200, (
                f"Expected /healthz to return 200, got {resp.status_code}."
            )
            return
        except Exception as exc:  # pragma: no cover - defensive
            last_exc = exc
            time.sleep(2)
    pytest.fail(
        f"Flaky API /healthz endpoint not reachable within 30s: {last_exc!r}"
    )


def test_user_project_files_exist():
    worker_py = os.path.join(PROJECT_DIR, "worker.py")
    trigger_py = os.path.join(PROJECT_DIR, "trigger.py")
    assert os.path.isfile(worker_py), f"Expected worker script at {worker_py}."
    assert os.path.isfile(trigger_py), f"Expected trigger script at {trigger_py}."


def test_trigger_succeeds_with_exponential_backoff(hatchet_worker):
    """Trigger the workflow and verify retry/backoff behavior end-to-end."""
    _reset_counter_file()

    env = os.environ.copy()

    t0 = time.monotonic()
    result = subprocess.run(
        ["python", "-u", "trigger.py"],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    t1 = time.monotonic()
    duration = t1 - t0

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
    assert parsed.get("ok") is True, (
        f"Expected task result 'ok' == true, got: {parsed!r}"
    )
    data_value = parsed.get("data")
    assert isinstance(data_value, str) and data_value, (
        f"Expected task result 'data' to be a non-empty string, got: {parsed!r}"
    )

    # The flaky server's counter file should now hold exactly 4
    # (3 failed calls + 1 successful call).
    assert COUNTER_FILE.is_file(), (
        f"Expected counter file {COUNTER_FILE} to exist after the task succeeded."
    )
    raw = COUNTER_FILE.read_text().strip()
    try:
        counter_value = int(raw)
    except ValueError:
        pytest.fail(
            f"Counter file {COUNTER_FILE} did not contain an integer; got: {raw!r}"
        )
    assert counter_value == 4, (
        f"Expected counter file {COUNTER_FILE} to contain 4 "
        "(3 failed flaky calls + 1 success), "
        f"got {counter_value}. The Hatchet task likely did not retry the right "
        "number of times."
    )

    # The total wall-clock duration must be large enough to show backoff slept
    # between retries. With retries=5 and backoff_factor=2.0 the minimum
    # cumulative sleep is ~14s, so 3s is a very conservative lower bound.
    assert duration >= MIN_DURATION_SEC, (
        f"trigger.py finished in {duration:.2f}s which is below the minimum "
        f"{MIN_DURATION_SEC}s expected for exponential backoff between Hatchet "
        "retries; backoff likely did not sleep between attempts."
    )
