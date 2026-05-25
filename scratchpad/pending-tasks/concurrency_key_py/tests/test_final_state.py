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
PAYMENTS_LOG = "/tmp/payments.log"
ENV_FILE = Path("/etc/zealt/hatchet.env")


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
        f"{timeout} seconds; cannot run the Hatchet concurrency test."
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
    # If the worker has not finished announcing its concurrency config to the
    # engine by the time the first trigger fires, the engine will run the task
    # without enforcing per-key concurrency and the assertions below will fail
    # spuriously.
    time.sleep(10)

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


def _run_trigger(user_id: str, amount: int):
    """Invoke trigger.py with the given input. Returns (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["python3", "-u", "trigger.py", "--user-id", user_id, "--amount", str(amount)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
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


@pytest.fixture(scope="session")
def concurrency_run(hatchet_worker):
    """Fire 4 parallel triggers and collect the results + the log file.

    This is a session-scoped fixture so individual assertions can inspect
    different aspects of the same run without re-paying the cost of executing
    the workflow runs multiple times.
    """
    # Start from a clean log file so we only see the lines produced by this run.
    if os.path.exists(PAYMENTS_LOG):
        os.remove(PAYMENTS_LOG)

    inputs = [
        ("u1", 100),
        ("u1", 200),
        ("u2", 300),
        ("u2", 400),
    ]

    triggers_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_run_trigger, uid, amt) for uid, amt in inputs]
        for fut in futures:
            triggers_results.append(fut.result())

    # Read the resulting log lines.
    log_lines: list[str] = []
    if os.path.exists(PAYMENTS_LOG):
        with open(PAYMENTS_LOG, "r", encoding="utf-8") as fh:
            log_lines = [ln.strip() for ln in fh.readlines() if ln.strip()]

    return {
        "inputs": inputs,
        "triggers": triggers_results,
        "log_lines": log_lines,
    }


def test_all_triggers_succeed(concurrency_run):
    for (uid, amt), (rc, stdout, stderr) in zip(
        concurrency_run["inputs"], concurrency_run["triggers"]
    ):
        assert rc == 0, (
            f"trigger.py --user-id {uid} --amount {amt} exited with code {rc}.\n"
            f"stdout:\n{stdout}\n\nstderr:\n{stderr}"
        )
        parsed = _parse_last_json(stdout)
        assert isinstance(parsed, dict), (
            f"Expected a JSON object from trigger.py for user_id={uid}, "
            f"got {type(parsed).__name__}: {parsed!r}"
        )
        assert parsed.get("userId") == uid, (
            f"Expected returned userId == {uid!r}, got {parsed!r}."
        )
        assert parsed.get("processed") is True, (
            f"Expected returned processed == true for user_id={uid}, got {parsed!r}."
        )


def _parse_log_line(line: str):
    """Parse a `<userId>:<amount>:<unix_ms_start>:<unix_ms_end>` line."""
    parts = line.split(":")
    assert len(parts) == 4, (
        f"Log line {line!r} did not have 4 colon-separated fields; got {len(parts)}."
    )
    user_id, amount_s, start_s, end_s = parts
    try:
        amount = int(amount_s)
        start = int(start_s)
        end = int(end_s)
    except ValueError as exc:  # pragma: no cover - failure path
        raise AssertionError(
            f"Log line {line!r} has non-integer fields: {exc}"
        )
    return user_id, amount, start, end


def test_payments_log_has_four_well_formed_lines(concurrency_run):
    lines = concurrency_run["log_lines"]
    assert len(lines) == 4, (
        f"Expected exactly 4 lines in {PAYMENTS_LOG}, found {len(lines)}.\n"
        f"Lines: {lines!r}"
    )
    pattern = re.compile(r"^[^:\s]+:\d+:\d+:\d+$")
    for ln in lines:
        assert pattern.match(ln), (
            f"Log line {ln!r} does not match the expected format "
            f"`<userId>:<amount>:<unix_ms_start>:<unix_ms_end>`."
        )

    for ln in lines:
        _user_id, _amount, start, end = _parse_log_line(ln)
        duration_ms = end - start
        assert duration_ms >= 2000, (
            f"Log line {ln!r} reports duration {duration_ms}ms, expected "
            ">= 2000ms (the task must sleep at least 2 seconds)."
        )


def _intervals_overlap(a, b):
    """Return True if intervals (start_a, end_a) and (start_b, end_b) overlap."""
    return max(a[0], b[0]) < min(a[1], b[1])


def test_same_user_intervals_do_not_overlap(concurrency_run):
    lines = concurrency_run["log_lines"]
    assert len(lines) == 4, (
        f"Expected exactly 4 lines in {PAYMENTS_LOG}, found {len(lines)}."
    )

    by_user: dict[str, list[tuple[int, int]]] = {}
    for ln in lines:
        user_id, _amount, start, end = _parse_log_line(ln)
        by_user.setdefault(user_id, []).append((start, end))

    for required_user in ("u1", "u2"):
        intervals = by_user.get(required_user, [])
        assert len(intervals) == 2, (
            f"Expected exactly 2 log entries for userId={required_user!r}, "
            f"found {len(intervals)}: {intervals!r}"
        )
        a, b = intervals
        assert not _intervals_overlap(a, b), (
            f"Concurrency limit violated for userId={required_user!r}: "
            f"the two intervals {a} and {b} overlap, but max_runs=1 keyed on "
            "userId should serialize them."
        )


def test_cross_user_intervals_overlap(concurrency_run):
    """Sanity check: cross-user concurrency must not be blocked."""
    lines = concurrency_run["log_lines"]
    by_user: dict[str, list[tuple[int, int]]] = {}
    for ln in lines:
        user_id, _amount, start, end = _parse_log_line(ln)
        by_user.setdefault(user_id, []).append((start, end))

    u1_intervals = by_user.get("u1", [])
    u2_intervals = by_user.get("u2", [])
    assert u1_intervals and u2_intervals, (
        "Expected log entries for both userId=u1 and userId=u2."
    )

    any_overlap = any(
        _intervals_overlap(a, b) for a in u1_intervals for b in u2_intervals
    )
    assert any_overlap, (
        "Expected at least one u1 interval to overlap with a u2 interval "
        "(proving cross-user concurrency is allowed), but all intervals were "
        f"serialized.\nu1: {u1_intervals}\nu2: {u2_intervals}"
    )
