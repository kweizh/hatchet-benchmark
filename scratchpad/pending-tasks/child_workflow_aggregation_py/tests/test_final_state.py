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
        timeout = 120
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
        timeout=240,
        env=os.environ.copy(),
    )
    return result


def test_worker_py_exists():
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    assert os.path.isfile(worker_path), f"Expected worker entrypoint at {worker_path}."


def test_run_py_exists():
    run_path = os.path.join(PROJECT_DIR, "run.py")
    assert os.path.isfile(run_path), f"Expected trigger script at {run_path}."


def test_aggregate_three_texts(hatchet_worker):
    result = _run_trigger(["hello world", "hatchet is fun", "ok"])
    assert result.returncode == 0, (
        "`python3 run.py 'hello world' 'hatchet is fun' 'ok'` exited with status "
        f"{result.returncode}.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    total_match = re.search(r"^Total:\s*6\s*$", result.stdout, re.MULTILINE)
    assert total_match is not None, (
        "Expected stdout to contain a line matching exactly `Total: 6`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    per_text_match = re.search(
        r"^PerText:\s*\[2,\s*3,\s*1\]\s*$", result.stdout, re.MULTILINE
    )
    assert per_text_match is not None, (
        "Expected stdout to contain a line matching exactly `PerText: [2, 3, 1]`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_aggregate_four_texts(hatchet_worker):
    result = _run_trigger(["one", "two three", "four five six", "seven"])
    assert result.returncode == 0, (
        "`python3 run.py 'one' 'two three' 'four five six' 'seven'` exited with status "
        f"{result.returncode}.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    total_match = re.search(r"^Total:\s*7\s*$", result.stdout, re.MULTILINE)
    assert total_match is not None, (
        "Expected stdout to contain a line matching exactly `Total: 7`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    per_text_match = re.search(
        r"^PerText:\s*\[1,\s*2,\s*3,\s*1\]\s*$", result.stdout, re.MULTILINE
    )
    assert per_text_match is not None, (
        "Expected stdout to contain a line matching exactly `PerText: [1, 2, 3, 1]`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_aggregate_single_text(hatchet_worker):
    result = _run_trigger(["single word"])
    assert result.returncode == 0, (
        "`python3 run.py 'single word'` exited with status "
        f"{result.returncode}.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    total_match = re.search(r"^Total:\s*2\s*$", result.stdout, re.MULTILINE)
    assert total_match is not None, (
        "Expected stdout to contain a line matching exactly `Total: 2`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    per_text_match = re.search(
        r"^PerText:\s*\[2\]\s*$", result.stdout, re.MULTILINE
    )
    assert per_text_match is not None, (
        "Expected stdout to contain a line matching exactly `PerText: [2]`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_parent_uses_child_spawning_api():
    """Sanity check that the parent delegates per-text counting to the
    `count_words` child via Hatchet's child-spawning API rather than
    computing it inline.
    """
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    with open(worker_path) as f:
        source = f.read()

    spawn_patterns = [
        r"count_words\.aio_run\s*\(",
        r"count_words\.aio_run_many\s*\(",
        r"count_words\.run\s*\(",
        r"count_words\.run_many\s*\(",
        r"spawn_workflow\s*\(\s*[\"']count_words[\"']",
        r"create_bulk_run_item\s*\(",
    ]
    matched = [p for p in spawn_patterns if re.search(p, source)]
    assert matched, (
        "Expected worker.py to invoke the `count_words` child via Hatchet's "
        "child-spawning API (e.g. `count_words.aio_run(...)`, "
        "`count_words.run(...)`, `aio_run_many`, `spawn_workflow(\"count_words\", ...)`), "
        "but none of those were found in the file.\n\nworker.py contents:\n"
        + source
    )


def test_count_words_is_a_workflow():
    """Sanity check that `count_words` is declared as a standalone Hatchet
    workflow object (via `hatchet.workflow(`), not solely as a bare
    `@hatchet.task` / `@hatchet.function` decorator.
    """
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    with open(worker_path) as f:
        source = f.read()

    # We accept either `hatchet.workflow(` with a name="count_words" mention,
    # or an explicit assignment `count_words = hatchet.workflow(`.
    pattern_assignment = re.search(
        r"count_words\s*=\s*\w+\.workflow\s*\(", source
    )
    pattern_named = re.search(
        r"\.workflow\s*\([^)]*name\s*=\s*[\"']count_words[\"']", source
    )
    assert pattern_assignment is not None or pattern_named is not None, (
        "Expected `count_words` to be declared as a standalone workflow object "
        "via `hatchet.workflow(name=\"count_words\", ...)` (e.g. "
        "`count_words = hatchet.workflow(name=\"count_words\", ...)`), but no "
        "such declaration was found.\n\nworker.py contents:\n" + source
    )
