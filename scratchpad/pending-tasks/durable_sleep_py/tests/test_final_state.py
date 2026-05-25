import json
import os
import re
import subprocess

PROJECT_DIR = "/home/user/myproject"
RESULT_FILE = "/tmp/result.json"


def _run_runner():
    """Remove any stale result and execute the runner end-to-end."""
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)
    runner = os.path.join(PROJECT_DIR, "run.py")
    assert os.path.isfile(runner), (
        f"Expected runner script at {runner}; the task must provide a runnable entrypoint."
    )
    result = subprocess.run(
        ["python3", runner],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        timeout=180,
    )
    assert result.returncode == 0, (
        "Runner exited with non-zero status.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_runner_produces_result_file():
    _run_runner()
    assert os.path.isfile(RESULT_FILE), (
        f"Expected result file {RESULT_FILE} to exist after running the runner."
    )
    assert os.path.getsize(RESULT_FILE) > 0, (
        f"Result file {RESULT_FILE} exists but is empty."
    )


def test_result_file_content_matches_expected_shape():
    assert os.path.isfile(RESULT_FILE), (
        f"Result file {RESULT_FILE} missing; the runner must produce it."
    )
    with open(RESULT_FILE, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected the JSON in {RESULT_FILE} to be an object, got: {type(data).__name__}."
    )
    assert data.get("message") == "wakeup", (
        f"Expected result['message'] == 'wakeup', got: {data.get('message')!r}."
    )
    assert "elapsed_sec" in data, (
        f"Expected result to include an 'elapsed_sec' field, got keys: {list(data.keys())}."
    )
    elapsed = data["elapsed_sec"]
    assert isinstance(elapsed, int) and not isinstance(elapsed, bool), (
        f"Expected 'elapsed_sec' to be an integer, got: {type(elapsed).__name__} ({elapsed!r})."
    )
    assert elapsed >= 5, (
        f"Expected 'elapsed_sec' to be >= 5 (durable sleep of ~5s), got: {elapsed}."
    )


def test_source_uses_hatchet_durable_sleep_api():
    """Inspect the project's Python sources to confirm Hatchet's durable sleep API is used."""
    py_sources = []
    for root, _dirs, files in os.walk(PROJECT_DIR):
        for name in files:
            if name.endswith(".py"):
                py_sources.append(os.path.join(root, name))
    assert py_sources, f"No Python source files found under {PROJECT_DIR}."

    combined = ""
    for path in py_sources:
        try:
            with open(path, "r") as f:
                combined += "\n" + f.read()
        except Exception:
            continue

    durable_decorator = re.search(
        r"@\s*[\w\.]*\.?durable_task\b|@\s*durable_task\b", combined
    )
    assert durable_decorator is not None, (
        "Could not find a '@durable_task' decorator in the project's Python sources; "
        "the task must be defined as a Hatchet durable task."
    )

    sleep_call = re.search(
        r"ctx\.(aio_sleep_for|sleep_for|aio_sleep|sleep)\s*\(", combined
    )
    assert sleep_call is not None, (
        "Could not find a durable sleep invocation "
        "(expected one of: ctx.aio_sleep_for(...), ctx.sleep_for(...), "
        "ctx.aio_sleep(...), or ctx.sleep(...)) in the project's Python sources."
    )
