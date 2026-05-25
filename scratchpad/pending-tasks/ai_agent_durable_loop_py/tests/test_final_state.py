import json
import os
import re
import subprocess
import time

import pytest
import requests
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
MOCK_LLM_URL = "http://127.0.0.1:9100"


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


@pytest.fixture(scope="session", autouse=True)
def _reset_mock_llm_counter():
    """Reset the mock LLM call counter so [DONE] fires deterministically on the 3rd call."""
    try:
        r = requests.post(f"{MOCK_LLM_URL}/reset", timeout=5)
        assert r.status_code == 200, f"Expected 200 from /reset, got {r.status_code}: {r.text}"
    except Exception as e:
        raise AssertionError(f"Could not reset mock LLM counter at {MOCK_LLM_URL}/reset: {e}")
    yield


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


def test_worker_uses_durable_sleep_api():
    """The worker source must call Hatchet's durable-sleep API, not a process-local sleep."""
    worker_path = os.path.join(PROJECT_DIR, "worker.py")
    with open(worker_path, "r") as f:
        src = f.read()
    assert ("aio_sleep_for" in src) or ("sleep_for" in src), (
        "worker.py must use Hatchet's durable-sleep API "
        "(e.g. ctx.aio_sleep_for(timedelta(seconds=1))). "
        f"worker.py contents:\n{src}"
    )


def test_task_registered_as_agent_loop(hatchet_worker):
    """The Hatchet task name must be exactly `agent_loop`."""
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
    assert "agent_loop" in names, (
        f"Expected a task/object named 'agent_loop' to be registered in worker.py. "
        f"Found names: {names}. stdout={result.stdout!r}"
    )


def test_trigger_returns_durable_agent_loop_result(hatchet_worker):
    """End-to-end: trigger the durable task and validate the conversation history + durable sleep."""
    # Reset the mock LLM counter immediately before running, so that this trigger's calls
    # start at 1 even if earlier tests/fixtures bumped it.
    r = requests.post(f"{MOCK_LLM_URL}/reset", timeout=5)
    assert r.status_code == 200, f"Could not reset mock LLM counter: {r.status_code} {r.text}"

    result = subprocess.run(
        ["python3", "trigger.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
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

    # --- Shape ---
    for key in ("messages", "turns", "start_ts", "end_ts", "elapsed_ms"):
        assert key in payload, f"Missing required field {key!r} in payload: {payload!r}"

    messages = payload["messages"]
    assert isinstance(messages, list), f"`messages` must be a list, got {type(messages).__name__}"
    assert len(messages) == 4, (
        f"Expected exactly 4 messages (1 user + 3 assistant), got {len(messages)}: {messages!r}"
    )

    # --- Initial user message preserved ---
    assert messages[0].get("role") == "user", f"messages[0] must have role 'user', got {messages[0]!r}"
    assert messages[0].get("content") == "hi", (
        f"messages[0] must have content 'hi', got {messages[0]!r}"
    )

    # --- Three assistant turns with the right prefix ---
    for idx in (1, 2, 3):
        msg = messages[idx]
        assert msg.get("role") == "assistant", (
            f"messages[{idx}] must have role 'assistant', got {msg!r}"
        )
        content = msg.get("content", "")
        assert isinstance(content, str), f"messages[{idx}].content must be a string, got {content!r}"
        assert re.match(rf"^{idx}: ", content), (
            f"messages[{idx}].content must start with prefix '{idx}: ', got {content!r}"
        )

    # --- [DONE] only on the 3rd assistant reply ---
    assert "[DONE]" not in messages[1]["content"], (
        f"messages[1].content must NOT contain [DONE]: {messages[1]['content']!r}"
    )
    assert "[DONE]" not in messages[2]["content"], (
        f"messages[2].content must NOT contain [DONE]: {messages[2]['content']!r}"
    )
    assert messages[3]["content"].rstrip().endswith("[DONE]"), (
        f"messages[3].content must end with '[DONE]', got {messages[3]['content']!r}"
    )

    # --- Turn count ---
    assert payload["turns"] == 3, f"Expected turns == 3, got {payload['turns']!r}"

    # --- Timestamps prove durable sleep happened ---
    start_ts = payload["start_ts"]
    end_ts = payload["end_ts"]
    elapsed_ms = payload["elapsed_ms"]
    for key, val in (("start_ts", start_ts), ("end_ts", end_ts), ("elapsed_ms", elapsed_ms)):
        assert isinstance(val, int), f"{key!r} must be an integer, got {type(val).__name__}: {val!r}"
    assert end_ts - start_ts == elapsed_ms, (
        f"end_ts - start_ts must equal elapsed_ms. "
        f"start_ts={start_ts}, end_ts={end_ts}, elapsed_ms={elapsed_ms}"
    )
    assert elapsed_ms >= 2000, (
        f"elapsed_ms must be >= 2000 ms (at least 2s of durable sleep across turns), "
        f"got: {elapsed_ms}"
    )
