import json
import os
import re
import subprocess

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = "/tmp/run_steps.log"
RESULT_FILE = "/tmp/result.json"

LOG_LINE_RE = re.compile(
    r"^step=(?P<step>step_a|step_b|step_c) worker_id=(?P<worker_id>\S+) hostname=(?P<hostname>\S+) pid=(?P<pid>\d+)$"
)


def _read_log_lines():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist after the workflow run."
    with open(LOG_FILE, "r") as f:
        raw = f.read()
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    return lines


def _read_result_json():
    assert os.path.isfile(RESULT_FILE), f"Expected result file {RESULT_FILE} to exist after the workflow run."
    with open(RESULT_FILE, "r") as f:
        return json.load(f)


def test_source_uses_sticky_strategy():
    """The implementation source must reference Hatchet's StickyStrategy."""
    result = subprocess.run(
        ["grep", "-R", "-q", "StickyStrategy", PROJECT_DIR],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected the project at {PROJECT_DIR} to reference 'StickyStrategy' "
        f"to configure sticky assignment, but no occurrence was found."
    )


def test_source_defines_dag_parents():
    """The implementation source must define DAG dependencies via parents=."""
    result = subprocess.run(
        ["grep", "-R", "-q", "parents=", PROJECT_DIR],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected the project at {PROJECT_DIR} to define a DAG using a "
        f"'parents=' argument on at least one task, but none was found."
    )


def test_source_spawns_two_workers():
    """The implementation source must spawn two distinct workers using either
    multiprocessing or subprocess, with two distinct WORKER_ID values."""
    # WORKER_ID env reference must exist
    r1 = subprocess.run(["grep", "-R", "-q", "WORKER_ID", PROJECT_DIR], capture_output=True, text=True)
    assert r1.returncode == 0, (
        f"Expected the project at {PROJECT_DIR} to reference 'WORKER_ID' "
        f"for distinguishing the two worker processes."
    )

    # Must use multiprocessing or subprocess to spawn workers
    r_mp = subprocess.run(["grep", "-R", "-q", "multiprocessing", PROJECT_DIR], capture_output=True, text=True)
    r_sp = subprocess.run(["grep", "-R", "-q", "subprocess", PROJECT_DIR], capture_output=True, text=True)
    assert r_mp.returncode == 0 or r_sp.returncode == 0, (
        f"Expected the project at {PROJECT_DIR} to spawn worker processes "
        f"using either 'multiprocessing' or 'subprocess', but neither was found."
    )

    # Two distinct worker id prefixes
    r_a = subprocess.run(["grep", "-R", "-q", "worker-A-", PROJECT_DIR], capture_output=True, text=True)
    r_b = subprocess.run(["grep", "-R", "-q", "worker-B-", PROJECT_DIR], capture_output=True, text=True)
    assert r_a.returncode == 0 and r_b.returncode == 0, (
        "Expected the project to define two distinct worker id literals "
        "with prefixes 'worker-A-' and 'worker-B-' in the source."
    )


def test_log_file_has_three_well_formed_lines():
    lines = _read_log_lines()
    assert len(lines) == 3, (
        f"Expected exactly 3 non-empty lines in {LOG_FILE}, got {len(lines)}: {lines!r}"
    )
    parsed = []
    for ln in lines:
        m = LOG_LINE_RE.match(ln)
        assert m, (
            f"Log line does not match expected format "
            f"'step=<name> worker_id=<id> hostname=<host> pid=<pid>': {ln!r}"
        )
        parsed.append(m.groupdict())

    steps_seen = {p["step"] for p in parsed}
    assert steps_seen == {"step_a", "step_b", "step_c"}, (
        f"Expected the three log lines to cover step_a, step_b, step_c exactly, "
        f"but observed steps: {steps_seen}"
    )


def test_log_file_sticky_assignment_honored():
    """All three steps must report the same worker_id (sticky)."""
    lines = _read_log_lines()
    worker_ids = []
    for ln in lines:
        m = LOG_LINE_RE.match(ln)
        assert m, f"Malformed log line: {ln!r}"
        worker_ids.append(m.group("worker_id"))
    assert len(set(worker_ids)) == 1, (
        f"Expected all three steps to run on the same worker_id (sticky assignment), "
        f"but observed worker_ids: {worker_ids}"
    )


def test_log_worker_id_matches_spawned_pattern():
    """Worker id must follow the worker-A-<run-id> / worker-B-<run-id> pattern."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID is not set; verifier cannot validate run-scoped worker id."

    lines = _read_log_lines()
    m = LOG_LINE_RE.match(lines[0])
    assert m, f"Malformed log line: {lines[0]!r}"
    worker_id = m.group("worker_id")

    expected_a = f"worker-A-{run_id}"
    expected_b = f"worker-B-{run_id}"
    assert worker_id in (expected_a, expected_b), (
        f"Observed worker_id {worker_id!r} does not match either of the spawned "
        f"worker ids {expected_a!r} or {expected_b!r}."
    )


def test_result_json_shape_and_consistency():
    data = _read_result_json()
    assert isinstance(data, dict) and "worker_ids" in data, (
        f"Expected {RESULT_FILE} to be a JSON object with a 'worker_ids' key, got: {data!r}"
    )
    worker_ids = data["worker_ids"]
    assert isinstance(worker_ids, list) and len(worker_ids) == 3, (
        f"Expected 'worker_ids' to be a list of length 3, got: {worker_ids!r}"
    )
    assert len(set(worker_ids)) == 1, (
        f"Expected all entries in 'worker_ids' to be identical (sticky), got: {worker_ids!r}"
    )

    # Cross-check with log file
    lines = _read_log_lines()
    m = LOG_LINE_RE.match(lines[0])
    log_worker_id = m.group("worker_id")
    assert worker_ids[0] == log_worker_id, (
        f"worker_ids[0]={worker_ids[0]!r} in {RESULT_FILE} does not match the "
        f"worker_id={log_worker_id!r} recorded in {LOG_FILE}."
    )
