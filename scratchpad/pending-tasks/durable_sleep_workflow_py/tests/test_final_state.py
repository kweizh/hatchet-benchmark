import json
import os
import re
import subprocess
import time

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"


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
    class Starter(ProcessStarter):
        name = "hatchet_worker"
        args = ["python3", "worker.py"]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True
        # Match common readiness signals emitted by Hatchet workers.
        pattern = r"(?i)(worker.*(started|listening|registered|running)|starting runner|listening for)"

    xprocess.ensure(Starter.name, Starter)
    # Give the worker a moment to fully register its task with the engine.
    time.sleep(3)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_worker_py_exists():
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    assert os.path.isfile(worker_path), f"Expected worker entrypoint at {worker_path}."


def test_trigger_py_exists():
    trigger_path = os.path.join(PROJECT_DIR, "trigger.py")
    assert os.path.isfile(trigger_path), f"Expected trigger entrypoint at {trigger_path}."


def test_trigger_returns_durable_sleep_result(hatchet_worker):
    """End-to-end: trigger the durable task and validate the elapsed_ms invariant."""
    result = subprocess.run(
        ["python3", "trigger.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, (
        f"`python3 trigger.py` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    match = re.search(r"^RESULT:\s*(\{.*\})\s*$", result.stdout, re.MULTILINE)
    assert match is not None, (
        "Expected stdout to contain a line matching `RESULT: { ...JSON... }`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    payload_str = match.group(1)
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        pytest.fail(f"RESULT line is not valid JSON: {payload_str!r} ({e})")

    for key in ("start_ts", "end_ts", "elapsed_ms"):
        assert key in payload, f"Missing required field {key!r} in result payload: {payload!r}"
        assert isinstance(payload[key], int), (
            f"Field {key!r} must be an integer, got {type(payload[key]).__name__}: {payload!r}"
        )

    start_ts = payload["start_ts"]
    end_ts = payload["end_ts"]
    elapsed_ms = payload["elapsed_ms"]

    assert end_ts - start_ts == elapsed_ms, (
        f"end_ts - start_ts must equal elapsed_ms. "
        f"start_ts={start_ts}, end_ts={end_ts}, elapsed_ms={elapsed_ms}"
    )
    assert 5000 <= elapsed_ms < 30000, (
        f"elapsed_ms must be >= 5000 and < 30000 (durable 5s sleep). got: {elapsed_ms}"
    )


def test_task_registered_as_delayed_greeter(hatchet_worker):
    """The Hatchet task name must be exactly `delayed_greeter`."""
    # Import the worker module from the project dir and inspect the registered
    # task object. Hatchet's Python SDK exposes the name on the task object.
    probe = (
        "import sys, json\n"
        f"sys.path.insert(0, {PROJECT_DIR!r})\n"
        "import worker as w\n"
        "names = []\n"
        "for attr in dir(w):\n"
        "    obj = getattr(w, attr)\n"
        "    for cand in ('name', '_name'):\n"
        "        v = getattr(obj, cand, None)\n"
        "        if isinstance(v, str):\n"
        "            names.append(v)\n"
        "print(json.dumps(names))\n"
    )
    result = subprocess.run(
        ["python3", "-c", probe],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, (
        f"Failed to import worker module: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    try:
        names = json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:
        names = []
    assert "delayed_greeter" in names, (
        f"Expected a task/object named 'delayed_greeter' to be registered in worker.py. "
        f"Found names: {names}. stdout={result.stdout!r}"
    )
