import os
import re
import socket
import time
from pathlib import Path

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/project"
ENV_FILE = Path("/etc/hatchet.env")
HEARTBEAT_LOG = "/tmp/heartbeat.log"
HEARTBEAT_LINE_RE = re.compile(
    r"^heartbeat \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)$"
)


def _wait_for_hatchet_env(timeout: float = 180.0) -> None:
    """Block until the container bootstrap finishes and the API token is ready.

    Loads the persisted env vars from /etc/hatchet.env into os.environ so that
    child processes (the user worker) inherit them.
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
        f"{timeout} seconds; cannot run the Hatchet cron-scheduled-task test."
    )


@pytest.fixture(scope="session", autouse=True)
def _ensure_hatchet_bootstrap():
    _wait_for_hatchet_env()
    # Remove any stale heartbeat log from a previous attempt so the verifier
    # only observes lines written by this run's worker.
    try:
        os.remove(HEARTBEAT_LOG)
    except FileNotFoundError:
        pass
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
        # Match common Hatchet worker startup log lines.
        pattern = r"(STARTING HATCHET|starting runner|listener|acquired action listener|registering worker|worker started|waiting for)"

    xprocess.ensure(Starter.name, Starter)

    # Give the gRPC registration a moment to settle before checking for cron fires.
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
    assert os.path.isfile(worker_py), f"Expected worker script at {worker_py}."


def test_cron_trigger_appends_heartbeat_lines(hatchet_worker):
    """Wait up to ~150 seconds for the cron to fire and append a heartbeat line.

    Hatchet runs cron jobs in UTC and a `* * * * *` expression fires once per
    minute. We give a generous window (well over one minute) to absorb cron
    alignment, gRPC registration, and engine scheduling latency.
    """
    deadline = time.time() + 150.0
    matched_lines: list[str] = []
    while time.time() < deadline:
        if os.path.isfile(HEARTBEAT_LOG):
            try:
                with open(HEARTBEAT_LOG, "r", encoding="utf-8", errors="replace") as fh:
                    contents = fh.read()
            except OSError:
                contents = ""
            lines = [ln.strip() for ln in contents.splitlines() if ln.strip()]
            matched_lines = [ln for ln in lines if HEARTBEAT_LINE_RE.match(ln)]
            if matched_lines:
                break
        time.sleep(2)

    assert os.path.isfile(HEARTBEAT_LOG), (
        f"Expected the cron-triggered task to create {HEARTBEAT_LOG}, but the "
        "file does not exist after waiting ~150 seconds."
    )
    assert matched_lines, (
        f"Expected at least one heartbeat line in {HEARTBEAT_LOG} matching "
        f"r'{HEARTBEAT_LINE_RE.pattern}', but found none. "
        f"File contents: {Path(HEARTBEAT_LOG).read_text(errors='replace')!r}"
    )


def test_heartbeat_log_lines_match_expected_format():
    """Every non-empty line in the heartbeat log must match the documented format."""
    assert os.path.isfile(HEARTBEAT_LOG), (
        f"Expected the cron-triggered task to create {HEARTBEAT_LOG}."
    )
    with open(HEARTBEAT_LOG, "r", encoding="utf-8", errors="replace") as fh:
        lines = [ln.strip() for ln in fh.read().splitlines() if ln.strip()]
    assert lines, f"Expected at least one line in {HEARTBEAT_LOG}, found none."
    bad = [ln for ln in lines if not HEARTBEAT_LINE_RE.match(ln)]
    assert not bad, (
        "Found heartbeat log lines that do not match the required format "
        f"'heartbeat <iso8601-utc-timestamp>'. Bad lines: {bad!r}"
    )
