import json
import os
import re
import subprocess
import time

import pytest
from xprocess import ProcessStarter


PROJECT_DIR = "/home/user/myproject"
WORKER_FILE = os.path.join(PROJECT_DIR, "worker.py")
BULK_FILE = os.path.join(PROJECT_DIR, "bulk.py")


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
        # Match common readiness signals emitted by Hatchet workers.
        pattern = (
            r"(?i)(worker.*(started|listening|registered|running)|"
            r"starting runner|listening for)"
        )

    xprocess.ensure(Starter.name, Starter)
    # Give the worker a moment to finish registering its task with the engine.
    time.sleep(3)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_worker_py_exists():
    assert os.path.isfile(WORKER_FILE), (
        f"Expected worker entrypoint at {WORKER_FILE}."
    )


def test_bulk_py_exists():
    assert os.path.isfile(BULK_FILE), (
        f"Expected bulk trigger script at {BULK_FILE}."
    )


def test_bulk_py_uses_bulk_run_api():
    """The trigger script MUST use one of Hatchet's bulk-run entry points.

    We accept any of: `run_many`, `aio_run_many`, `run_many_no_wait`,
    or `aio_run_many_no_wait`. We also reject the case where the script
    only contains per-element `.run(` / `.aio_run(` calls.
    """
    with open(BULK_FILE) as f:
        source = f.read()

    bulk_patterns = [
        r"\.run_many\s*\(",
        r"\.aio_run_many\s*\(",
        r"\.run_many_no_wait\s*\(",
        r"\.aio_run_many_no_wait\s*\(",
    ]
    matched = [p for p in bulk_patterns if re.search(p, source)]
    assert matched, (
        "Expected bulk.py to use one of Hatchet's bulk-run entry points "
        "(`run_many`, `aio_run_many`, `run_many_no_wait`, or "
        "`aio_run_many_no_wait`), but none of those were found.\n\n"
        "bulk.py contents:\n" + source
    )


def test_bulk_run_produces_expected_results(hatchet_worker):
    """Trigger 25 runs via bulk.py and verify the JSON results."""
    env = os.environ.copy()
    result = subprocess.run(
        ["python3", "bulk.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=240,
        env=env,
    )
    assert result.returncode == 0, (
        f"`python3 bulk.py` exited with status {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    # Find a line of the form: `Results: [...]`
    match = re.search(
        r"^Results:\s*(\[.*\])\s*$",
        result.stdout,
        re.MULTILINE,
    )
    assert match is not None, (
        "Expected bulk.py stdout to contain a line of the form "
        "`Results: <json-array>`.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    payload = match.group(1)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"Failed to parse `Results:` JSON payload: {exc}.\n"
            f"Payload was: {payload!r}\n"
            f"stdout:\n{result.stdout}"
        )

    assert isinstance(data, list), (
        f"Expected `Results:` payload to be a JSON list, got {type(data).__name__}."
    )
    assert len(data) == 25, (
        f"Expected exactly 25 results, got {len(data)}: {data!r}"
    )

    for item in data:
        assert isinstance(item, dict), (
            f"Each result must be a JSON object, got {type(item).__name__}: {item!r}"
        )
        assert set(item.keys()) == {"i", "squared"}, (
            f"Each result must have exactly keys 'i' and 'squared', got "
            f"{sorted(item.keys())!r} (item={item!r})."
        )
        assert isinstance(item["i"], int) and not isinstance(item["i"], bool), (
            f"Field 'i' must be an integer, got {type(item['i']).__name__} in {item!r}."
        )
        assert (
            isinstance(item["squared"], int) and not isinstance(item["squared"], bool)
        ), (
            f"Field 'squared' must be an integer, got "
            f"{type(item['squared']).__name__} in {item!r}."
        )

    sorted_data = sorted(data, key=lambda d: d["i"])
    expected = [{"i": k, "squared": k * k} for k in range(25)]
    assert sorted_data == expected, (
        "Sorted bulk-run results do not match the expected sequence "
        "[{'i': 0, 'squared': 0}, ..., {'i': 24, 'squared': 576}].\n"
        f"Got: {sorted_data!r}"
    )
