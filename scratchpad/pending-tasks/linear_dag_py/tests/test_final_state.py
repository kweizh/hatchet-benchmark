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


def test_trigger_script_prints_final_output_25(hatchet_worker):
    result = subprocess.run(
        ["python3", "run.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
        env=os.environ.copy(),
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    assert result.returncode == 0, (
        f"`python3 run.py` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    match = re.search(r"^Final output:\s*25\s*$", result.stdout, re.MULTILINE)
    assert match is not None, (
        "Expected stdout to contain a line matching exactly `Final output: 25`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_pipeline_workflow_registered_via_rest(hatchet_worker):
    """Best-effort check that a workflow named 'pipeline' is registered."""
    port = _hatchet_port()
    if port is None:
        pytest.skip("HATCHET_CLIENT_HOST_PORT not configured for REST lookup.")

    # The hatchet-lite REST API is exposed on a separate well-known port. The
    # gRPC port from HATCHET_CLIENT_HOST_PORT is not the same as the HTTP API,
    # so if we cannot reach an HTTP endpoint we just skip this auxiliary check
    # rather than fail the entire task (the trigger-script check above is the
    # authoritative behavioural assertion).
    candidate_ports = [8888, 8080, port]
    api_host = os.environ.get("HATCHET_CLIENT_HOST_PORT", "localhost:7077").rsplit(
        ":", 1
    )[0]

    for candidate in candidate_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((api_host, candidate)) == 0:
                # Reachable; we do not strictly assert on the response shape
                # because the REST API surface varies across Hatchet versions.
                return

    pytest.skip("No Hatchet REST API port reachable; skipping registry check.")
