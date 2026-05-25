import os
import re
import socket
import subprocess
import time

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"


def _hatchet_port():
    host_port = os.environ.get("HATCHET_CLIENT_HOST_PORT", "")
    if ":" not in host_port:
        return None
    _host, port_str = host_port.rsplit(":", 1)
    try:
        return int(port_str)
    except ValueError:
        return None


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
        # Match a few common readiness signals emitted by Hatchet workers.
        pattern = r"(?i)(worker.*(started|listening|registered|running)|starting runner|listening for)"

    xprocess.ensure(Starter.name, Starter)
    # Give the worker a moment to fully register its workflow with the engine.
    time.sleep(3)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_worker_py_exists():
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    assert os.path.isfile(worker_path), f"Expected worker entrypoint at {worker_path}."


def test_run_py_exists():
    run_path = os.path.join(PROJECT_DIR, "run.py")
    assert os.path.isfile(run_path), f"Expected trigger script at {run_path}."


def test_trigger_script_prints_final_sum_37(hatchet_worker):
    result = subprocess.run(
        ["python3", "run.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, (
        f"`python3 run.py` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    match = re.search(r"^Final sum:\s*37\s*$", result.stdout, re.MULTILINE)
    assert match is not None, (
        "Expected stdout to contain a line matching exactly `Final sum: 37`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_branch_values_visible_in_workflow_output(hatchet_worker):
    """Verify left=20 and right=17 are present somewhere in the trigger output.

    The trigger script `run.py` returns the full task-keyed result mapping from
    `diamond.run()` (e.g. {"step_root": {...}, "step_left": {"value": 20},
    "step_right": {"value": 17}, "step_join": {"sum": 37}}). We rely on the
    agent surfacing those values so we can assert that both branches actually
    ran with base=10 as required by `truth`.
    """
    result = subprocess.run(
        ["python3", "run.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, (
        f"`python3 run.py` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    combined = result.stdout
    assert "20" in combined, (
        "Expected step_left output value 20 (= base * 2 with base=10) to appear "
        f"in the trigger output.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    assert "17" in combined, (
        "Expected step_right output value 17 (= base + 7 with base=10) to appear "
        f"in the trigger output.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_hatchet_engine_reachable_for_workflow(hatchet_worker):
    """Best-effort check that the Hatchet engine is reachable."""
    port = _hatchet_port()
    if port is None:
        pytest.skip("HATCHET_CLIENT_HOST_PORT not configured.")
    host = os.environ.get("HATCHET_CLIENT_HOST_PORT", "localhost:7077").rsplit(":", 1)[0]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        connected = sock.connect_ex((host, port)) == 0
    assert connected, f"Hatchet engine not reachable at {host}:{port}."
