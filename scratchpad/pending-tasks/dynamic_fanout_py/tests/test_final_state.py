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
        timeout = 90
        terminate_on_interrupt = True
        # Match a few common readiness signals emitted by Hatchet workers.
        pattern = r"(?i)(worker.*(started|listening|registered|running)|starting runner|listening for)"

    xprocess.ensure(Starter.name, Starter)
    # Give the worker a moment to fully register its workflows with the engine.
    time.sleep(3)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def _run_trigger(args):
    result = subprocess.run(
        ["python3", "run.py", *[str(a) for a in args]],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
        env=os.environ.copy(),
    )
    return result


def test_worker_py_exists():
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    assert os.path.isfile(worker_path), f"Expected worker entrypoint at {worker_path}."


def test_run_py_exists():
    run_path = os.path.join(PROJECT_DIR, "run.py")
    assert os.path.isfile(run_path), f"Expected trigger script at {run_path}."


def test_fanout_squares_one_to_five(hatchet_worker):
    result = _run_trigger([1, 2, 3, 4, 5])
    assert result.returncode == 0, (
        f"`python3 run.py 1 2 3 4 5` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    match = re.search(
        r"^Squares:\s*\[1,\s*4,\s*9,\s*16,\s*25\]\s*$",
        result.stdout,
        re.MULTILINE,
    )
    assert match is not None, (
        "Expected stdout to contain a line matching exactly `Squares: [1, 4, 9, 16, 25]`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_fanout_squares_unsorted_input(hatchet_worker):
    result = _run_trigger([7, 3, 5])
    assert result.returncode == 0, (
        f"`python3 run.py 7 3 5` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    match = re.search(
        r"^Squares:\s*\[9,\s*25,\s*49\]\s*$",
        result.stdout,
        re.MULTILINE,
    )
    assert match is not None, (
        "Expected stdout to contain a line matching exactly `Squares: [9, 25, 49]` "
        "(squares of 3,5,7 sorted ascending).\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_fanout_squares_with_zero_and_negative(hatchet_worker):
    result = _run_trigger([0, -2, 4])
    assert result.returncode == 0, (
        f"`python3 run.py 0 -2 4` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    match = re.search(
        r"^Squares:\s*\[0,\s*4,\s*16\]\s*$",
        result.stdout,
        re.MULTILINE,
    )
    assert match is not None, (
        "Expected stdout to contain a line matching exactly `Squares: [0, 4, 16]`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_parent_uses_child_spawning_api():
    """Sanity check that the parent delegates squaring to the child workflow
    via Hatchet's child-spawning API rather than computing it inline.

    We only require that ONE of the well-known spawn entry points appears in
    the worker source. We do not enforce a specific call signature.
    """
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    with open(worker_path) as f:
        source = f.read()

    spawn_patterns = [
        r"\.aio_run\s*\(",
        r"\.aio_run_many\s*\(",
        r"\.run\s*\(",
        r"\.run_many\s*\(",
        r"spawn_workflow\s*\(",
        r"create_bulk_run_item\s*\(",
    ]
    matched = [p for p in spawn_patterns if re.search(p, source)]
    assert matched, (
        "Expected worker.py to invoke the `square` child via Hatchet's "
        "child-spawning API (e.g. `square.aio_run(...)`, `square.run(...)`, "
        "`aio_run_many`, `spawn_workflow(...)`), but none of those were found "
        "in the file.\n\nworker.py contents:\n" + source
    )
