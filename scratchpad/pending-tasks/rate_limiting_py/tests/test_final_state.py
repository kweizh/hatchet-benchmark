import concurrent.futures
import json
import os
import re
import socket
import subprocess
import time
from pathlib import Path

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
RATE_LOG = "/tmp/rate.log"
ENV_FILE = Path("/etc/zealt/hatchet.env")
RATE_LIMIT_KEY = "external_api"


def _wait_for_hatchet_env(timeout: float = 180.0) -> None:
    """Block until the container bootstrap finishes and the API token is ready.

    Loads the persisted env vars from /etc/zealt/hatchet.env into os.environ so
    that child processes (the user worker + triggers) inherit them.
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
        "Container bootstrap (/etc/zealt/hatchet.env) did not become ready within "
        f"{timeout} seconds; cannot run the Hatchet rate-limit test."
    )


@pytest.fixture(scope="session", autouse=True)
def _ensure_hatchet_bootstrap():
    _wait_for_hatchet_env()
    yield


@pytest.fixture(scope="session", autouse=True)
def _kill_stale_workers():
    subprocess.run(
        ["pkill", "-f", "python3 worker.py"],
        check=False,
        capture_output=True,
    )
    yield
    subprocess.run(
        ["pkill", "-f", "python3 worker.py"],
        check=False,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def hatchet_worker(xprocess):
    """Start the user's Hatchet worker in the background for the test session."""

    class Starter(ProcessStarter):
        name = "hatchet_worker"
        args = ["python3", "-u", "worker.py"]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True
        # Match common Hatchet worker startup log lines.
        pattern = (
            r"(STARTING HATCHET|starting runner|listener|acquired action listener|"
            r"registering worker|worker started|listening for|waiting for)"
        )

    xprocess.ensure(Starter.name, Starter)

    # Give the gRPC registration a generous moment to settle before triggering.
    # The worker must have time to declare the static rate limit and announce
    # its task config to the engine, otherwise the first batch will not be
    # rate-limited correctly.
    time.sleep(12)

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


def _run_trigger():
    """Invoke trigger.py. Returns (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["python3", "-u", "trigger.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        env=os.environ.copy(),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _parse_last_json(stdout: str):
    last_error: Exception | None = None
    for ln in reversed([l.strip() for l in stdout.splitlines() if l.strip()]):
        try:
            return json.loads(ln)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
    raise AssertionError(
        f"Could not find a JSON object on trigger.py stdout. Last error: {last_error}\n"
        f"stdout was:\n{stdout}"
    )


def _get_rate_limit_entry():
    """Return the `external_api` rate-limit entry via the Hatchet SDK, or None."""
    from hatchet_sdk import Hatchet

    h = Hatchet()
    listing = h.rate_limits.list()
    rows = getattr(listing, "rows", None) or []
    for row in rows:
        if getattr(row, "key", None) == RATE_LIMIT_KEY:
            return row
    return None


def _read_log_lines():
    if not os.path.exists(RATE_LOG):
        return []
    with open(RATE_LOG, "r", encoding="utf-8") as fh:
        return [ln.strip() for ln in fh.readlines() if ln.strip()]


@pytest.fixture(scope="session")
def rate_limit_run(hatchet_worker):
    """Two-batch rate-limit experiment.

    Fires 3 triggers in parallel (batch 1), checks the rate-limit value drops
    to 0, sleeps for the window to refill, then fires 3 more triggers (batch 2)
    and checks that the rate-limit value refills back to 3.
    """
    # Start from a clean log file so we only see lines produced by this run.
    if os.path.exists(RATE_LOG):
        os.remove(RATE_LOG)

    # --- Batch 1: 3 parallel triggers ---
    batch1_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_run_trigger) for _ in range(3)]
        for fut in futures:
            batch1_results.append(fut.result())

    log_lines_after_batch1 = _read_log_lines()

    # Sleep briefly so the engine has a chance to record consumption before we
    # query the rate-limit state.
    time.sleep(2)
    rate_limit_after_batch1 = _get_rate_limit_entry()

    # Sleep ~70 seconds to let the 1-minute window refill.
    time.sleep(70)

    rate_limit_after_refill = _get_rate_limit_entry()

    # --- Batch 2: 3 parallel triggers ---
    batch2_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_run_trigger) for _ in range(3)]
        for fut in futures:
            batch2_results.append(fut.result())

    log_lines_final = _read_log_lines()

    return {
        "batch1_results": batch1_results,
        "batch2_results": batch2_results,
        "log_lines_after_batch1": log_lines_after_batch1,
        "log_lines_final": log_lines_final,
        "rate_limit_after_batch1": rate_limit_after_batch1,
        "rate_limit_after_refill": rate_limit_after_refill,
    }


def test_rate_limit_is_registered(hatchet_worker):
    """The worker must have declared the `external_api` static rate limit at startup."""
    entry = _get_rate_limit_entry()
    assert entry is not None, (
        f"Expected a static rate limit with key={RATE_LIMIT_KEY!r} to be "
        "registered with the Hatchet engine, but rate_limits.list() returned none."
    )
    assert getattr(entry, "limit_value", None) == 3, (
        f"Expected limit_value=3 for rate limit {RATE_LIMIT_KEY!r}, "
        f"got {getattr(entry, 'limit_value', None)!r}."
    )
    window = (getattr(entry, "window", "") or "").upper()
    assert "MINUTE" in window or "1 MINUTE" in window, (
        f"Expected the rate-limit window for {RATE_LIMIT_KEY!r} to be 1 MINUTE, "
        f"got window={window!r}."
    )


def test_batch1_all_succeed(rate_limit_run):
    triggers = rate_limit_run["batch1_results"]
    assert len(triggers) == 3, (
        f"Expected 3 trigger results in batch 1, got {len(triggers)}."
    )
    for idx, (rc, stdout, stderr) in enumerate(triggers):
        assert rc == 0, (
            f"batch1 trigger.py run #{idx} exited with code {rc}.\n"
            f"stdout:\n{stdout}\n\nstderr:\n{stderr}"
        )
        parsed = _parse_last_json(stdout)
        assert isinstance(parsed, dict), (
            f"Expected a JSON object from batch1 trigger.py run #{idx}, "
            f"got {type(parsed).__name__}: {parsed!r}"
        )
        assert parsed.get("ok") is True, (
            f"Expected returned ok == true for batch1 run #{idx}, got {parsed!r}."
        )


def test_batch1_log_has_three_lines(rate_limit_run):
    lines = rate_limit_run["log_lines_after_batch1"]
    assert len(lines) == 3, (
        f"Expected exactly 3 lines in {RATE_LOG} after batch 1, found {len(lines)}.\n"
        f"Lines: {lines!r}"
    )
    pattern = re.compile(r"^\d+$")
    for ln in lines:
        assert pattern.match(ln), (
            f"Log line {ln!r} does not match the expected format "
            f"`<integer_millisecond_timestamp>`."
        )

    timestamps = sorted(int(ln) for ln in lines)
    spread_ms = timestamps[-1] - timestamps[0]
    assert spread_ms <= 10000, (
        f"Expected the first 3 runs (within budget) to start within ~10s of "
        f"each other, but spread was {spread_ms}ms. Timestamps: {timestamps!r}"
    )


def test_rate_limit_value_drops_to_zero_after_batch1(rate_limit_run):
    entry = rate_limit_run["rate_limit_after_batch1"]
    assert entry is not None, (
        f"Expected the rate limit {RATE_LIMIT_KEY!r} to still be registered "
        "after batch 1, but it was not found."
    )
    value = getattr(entry, "value", None)
    assert value == 0, (
        f"Expected the rate-limit value for {RATE_LIMIT_KEY!r} to be 0 after "
        f"3 task runs consumed 1 unit each, got value={value!r}."
    )


def test_rate_limit_refills_after_window(rate_limit_run):
    entry = rate_limit_run["rate_limit_after_refill"]
    assert entry is not None, (
        f"Expected the rate limit {RATE_LIMIT_KEY!r} to still be registered "
        "after the refill wait, but it was not found."
    )
    value = getattr(entry, "value", None)
    assert value == 3, (
        f"Expected the rate-limit value for {RATE_LIMIT_KEY!r} to refill to 3 "
        f"after the 1-minute window elapsed, got value={value!r}."
    )


def test_batch2_all_succeed(rate_limit_run):
    triggers = rate_limit_run["batch2_results"]
    assert len(triggers) == 3, (
        f"Expected 3 trigger results in batch 2, got {len(triggers)}."
    )
    for idx, (rc, stdout, stderr) in enumerate(triggers):
        assert rc == 0, (
            f"batch2 trigger.py run #{idx} exited with code {rc}.\n"
            f"stdout:\n{stdout}\n\nstderr:\n{stderr}"
        )
        parsed = _parse_last_json(stdout)
        assert isinstance(parsed, dict), (
            f"Expected a JSON object from batch2 trigger.py run #{idx}, "
            f"got {type(parsed).__name__}: {parsed!r}"
        )
        assert parsed.get("ok") is True, (
            f"Expected returned ok == true for batch2 run #{idx}, got {parsed!r}."
        )


def test_final_log_has_six_lines_with_window_gap(rate_limit_run):
    lines = rate_limit_run["log_lines_final"]
    assert len(lines) == 6, (
        f"Expected exactly 6 lines in {RATE_LOG} after both batches, "
        f"found {len(lines)}. Lines: {lines!r}"
    )
    pattern = re.compile(r"^\d+$")
    for ln in lines:
        assert pattern.match(ln), (
            f"Log line {ln!r} does not match the expected format "
            f"`<integer_millisecond_timestamp>`."
        )

    timestamps = sorted(int(ln) for ln in lines)
    # batch 1 is t[0..2], batch 2 is t[3..5]; the boundary gap should be >=50s.
    boundary_gap_ms = timestamps[3] - timestamps[2]
    assert boundary_gap_ms >= 50000, (
        f"Expected the gap between the last batch-1 timestamp (t[2]) and the "
        f"first batch-2 timestamp (t[3]) to be at least 50s (reflecting the "
        f"1-minute rate-limit window refill), but the gap was "
        f"{boundary_gap_ms}ms. Timestamps: {timestamps!r}"
    )
