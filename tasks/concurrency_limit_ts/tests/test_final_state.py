import os
import re
import signal
import subprocess
import time
from pathlib import Path

import pytest

PROJECT_DIR = "/home/user/myproject"
RUN_ID = os.environ.get("ZEALT_RUN_ID", "").strip()
LOG_FILE = f"/tmp/orders-{RUN_ID}.log"
WORKER_READY_WAIT_SECONDS = 15
RUNNER_TIMEOUT_SECONDS = 60
SLEEP_FLOOR_MS = 1400  # 1500ms - 100ms wiggle
PARALLELISM_BUDGET_MS = int(4 * 1500 * 0.9)  # 5400 ms


@pytest.fixture(scope="session")
def run_id():
    assert RUN_ID, "ZEALT_RUN_ID environment variable must be set."
    return RUN_ID


@pytest.fixture(scope="session")
def run_pipeline(run_id):
    """Start the worker, run the runner, then collect timing and log lines."""
    # Clean stale log file.
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    env = os.environ.copy()

    # Start the worker as a background process group so we can terminate cleanly.
    worker_log_path = "/tmp/worker.stdout.log"
    worker_log = open(worker_log_path, "w")
    worker_proc = subprocess.Popen(
        ["pnpm", "run", "worker"],
        cwd=PROJECT_DIR,
        env=env,
        stdout=worker_log,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )

    try:
        # Give the worker time to register with Hatchet Cloud.
        time.sleep(WORKER_READY_WAIT_SECONDS)
        assert worker_proc.poll() is None, (
            f"Worker process exited prematurely. See {worker_log_path}."
        )

        # Run the runner and measure wallclock time.
        wallclock_start = time.monotonic()
        runner_result = subprocess.run(
            ["pnpm", "run", "runner"],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=RUNNER_TIMEOUT_SECONDS,
        )
        wallclock_end = time.monotonic()
        elapsed_runner_ms = int((wallclock_end - wallclock_start) * 1000)

        assert runner_result.returncode == 0, (
            f"Runner exited with non-zero status {runner_result.returncode}.\n"
            f"stdout:\n{runner_result.stdout}\nstderr:\n{runner_result.stderr}"
        )

        yield {
            "elapsed_runner_ms": elapsed_runner_ms,
            "runner_stdout": runner_result.stdout,
            "runner_stderr": runner_result.stderr,
        }
    finally:
        try:
            os.killpg(os.getpgid(worker_proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            worker_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(worker_proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        worker_log.close()


@pytest.fixture(scope="session")
def log_entries(run_pipeline, run_id):
    """Parse /tmp/orders-<run-id>.log into structured entries."""
    assert os.path.isfile(LOG_FILE), f"Expected log file at {LOG_FILE} after runner."
    raw = Path(LOG_FILE).read_text()
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    line_re = re.compile(r"^(start|end)\s+((?:US|EU)-zr-[a-z0-9]+)\s+(\d+)$")
    entries = []
    for ln in lines:
        m = line_re.match(ln)
        assert m, f"Log line {ln!r} does not match expected format 'phase region epochMs'."
        phase, region, ts = m.group(1), m.group(2), int(m.group(3))
        entries.append({"phase": phase, "region": region, "ts": ts, "raw": ln})
    return entries


def _intervals_for_region(entries, region):
    starts = sorted(e["ts"] for e in entries if e["phase"] == "start" and e["region"] == region)
    ends = sorted(e["ts"] for e in entries if e["phase"] == "end" and e["region"] == region)
    assert len(starts) == 2 and len(ends) == 2, (
        f"Expected exactly 2 start/end pairs for region {region}, got "
        f"starts={starts} ends={ends}."
    )
    # With maxRuns=1, intervals must not overlap. Pair earliest start with earliest end.
    return [(starts[0], ends[0]), (starts[1], ends[1])]


def test_log_has_eight_entries(log_entries):
    assert len(log_entries) == 8, (
        f"Expected exactly 8 log lines (4 starts + 4 ends), got {len(log_entries)}: "
        f"{[e['raw'] for e in log_entries]}"
    )


def test_log_phase_counts(log_entries):
    starts = [e for e in log_entries if e["phase"] == "start"]
    ends = [e for e in log_entries if e["phase"] == "end"]
    assert len(starts) == 4, f"Expected 4 start lines, got {len(starts)}."
    assert len(ends) == 4, f"Expected 4 end lines, got {len(ends)}."


def test_log_per_region_counts(log_entries, run_id):
    us_region = f"US-{run_id}"
    eu_region = f"EU-{run_id}"
    us = [e for e in log_entries if e["region"] == us_region]
    eu = [e for e in log_entries if e["region"] == eu_region]
    assert len(us) == 4, f"Expected 4 log lines for {us_region}, got {len(us)}: {us}"
    assert len(eu) == 4, f"Expected 4 log lines for {eu_region}, got {len(eu)}: {eu}"


def test_us_intervals_do_not_overlap(log_entries, run_id):
    us_region = f"US-{run_id}"
    intervals = _intervals_for_region(log_entries, us_region)
    (s1, e1), (s2, e2) = intervals
    # Intervals are sorted by start. The first must end before the second starts.
    assert e1 <= s2, (
        f"US intervals overlap: [{s1}, {e1}] and [{s2}, {e2}]. "
        f"With maxRuns=1 keyed on region, runs for the same region must be serialized."
    )


def test_eu_intervals_do_not_overlap(log_entries, run_id):
    eu_region = f"EU-{run_id}"
    intervals = _intervals_for_region(log_entries, eu_region)
    (s1, e1), (s2, e2) = intervals
    assert e1 <= s2, (
        f"EU intervals overlap: [{s1}, {e1}] and [{s2}, {e2}]. "
        f"With maxRuns=1 keyed on region, runs for the same region must be serialized."
    )


def test_each_interval_sleeps_at_least_1400ms(log_entries, run_id):
    for region in (f"US-{run_id}", f"EU-{run_id}"):
        for (s, e) in _intervals_for_region(log_entries, region):
            duration = e - s
            assert duration >= SLEEP_FLOOR_MS, (
                f"Interval for {region} [{s}, {e}] is only {duration} ms; "
                f"expected at least {SLEEP_FLOOR_MS} ms (~1.5s sleep)."
            )


def test_cross_region_parallelism(log_entries):
    """Total elapsed across all 4 runs must be < 4 * 1.5s * 0.9 = 5400 ms.

    This proves US and EU groups ran in parallel rather than fully sequentially.
    """
    all_starts = [e["ts"] for e in log_entries if e["phase"] == "start"]
    all_ends = [e["ts"] for e in log_entries if e["phase"] == "end"]
    total = max(all_ends) - min(all_starts)
    assert total < PARALLELISM_BUDGET_MS, (
        f"Total elapsed wallclock from log was {total} ms, expected < "
        f"{PARALLELISM_BUDGET_MS} ms. This indicates US and EU runs did not "
        f"execute in parallel across regions."
    )
