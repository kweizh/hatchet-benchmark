import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
DOC_ID = "d1"
DOC_CONTENT = "hello world foo bar baz"
EXPECTED_WORD_COUNT = 5
DOC_DIR = f"/tmp/docs/{DOC_ID}"


def _parse_iso8601(value):
    """Return a datetime if the value is a valid ISO 8601 timestamp, else None."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    # Python 3.11+ accepts most ISO 8601 strings (including trailing 'Z') via
    # fromisoformat. Fall back to a manual 'Z' -> '+00:00' rewrite for older
    # behaviour and edge cases.
    try:
        return dt.datetime.fromisoformat(candidate)
    except ValueError:
        pass
    try:
        return dt.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None


@pytest.fixture(scope="session", autouse=True)
def _clean_state():
    # Kill any leftover workers from a previous run.
    subprocess.run(
        ["pkill", "-f", "python3 worker.py"],
        check=False,
        capture_output=True,
    )
    # Wipe any leftover artifacts so this test's checks are not satisfied by
    # an earlier run.
    if os.path.isdir(DOC_DIR):
        shutil.rmtree(DOC_DIR, ignore_errors=True)
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
        pattern = r"(?i)(worker.*(started|listening|registered|running)|starting runner|listening for)"

    xprocess.ensure(Starter.name, Starter)
    # Give the worker a moment to fully register its workflow with the engine.
    time.sleep(3)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


@pytest.fixture(scope="session")
def trigger_result(hatchet_worker):
    """Run the trigger command exactly once and reuse its output across tests."""
    result = subprocess.run(
        ["python3", "run.py", DOC_ID, DOC_CONTENT],
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


def test_trigger_exits_successfully(trigger_result):
    assert trigger_result.returncode == 0, (
        f"`python3 run.py {DOC_ID} <content>` exited with status {trigger_result.returncode}.\n"
        f"stdout:\n{trigger_result.stdout}\n\nstderr:\n{trigger_result.stderr}"
    )


def test_trigger_prints_index_line(trigger_result):
    match = re.search(r"^INDEX:\s*(\{.*\})\s*$", trigger_result.stdout, re.MULTILINE)
    assert match is not None, (
        "Expected stdout to contain a line of the form `INDEX: {<json>}`.\n"
        f"stdout:\n{trigger_result.stdout}\n\nstderr:\n{trigger_result.stderr}"
    )
    payload = match.group(1)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        pytest.fail(f"INDEX line did not contain valid JSON: {exc!s}. Payload: {payload!r}")
    assert isinstance(parsed, dict), f"INDEX payload must be a JSON object, got: {parsed!r}"
    assert parsed.get("doc_id") == DOC_ID, (
        f"Expected INDEX payload doc_id == {DOC_ID!r}, got: {parsed.get('doc_id')!r} in {parsed!r}"
    )
    assert parsed.get("word_count") == EXPECTED_WORD_COUNT, (
        f"Expected INDEX payload word_count == {EXPECTED_WORD_COUNT}, "
        f"got: {parsed.get('word_count')!r} in {parsed!r}"
    )
    indexed_at = parsed.get("indexed_at")
    assert _parse_iso8601(indexed_at) is not None, (
        f"Expected INDEX payload indexed_at to be a valid ISO 8601 timestamp, "
        f"got: {indexed_at!r} in {parsed!r}"
    )


def test_doc_dir_contains_four_artifacts(trigger_result):
    assert os.path.isdir(DOC_DIR), (
        f"Expected per-document directory {DOC_DIR} to exist after pipeline run.\n"
        f"trigger stdout:\n{trigger_result.stdout}\n\nstderr:\n{trigger_result.stderr}"
    )
    entries = [
        name
        for name in os.listdir(DOC_DIR)
        if os.path.isfile(os.path.join(DOC_DIR, name))
    ]
    assert len(entries) == 4, (
        f"Expected exactly 4 artifact files under {DOC_DIR} (one per pipeline stage), "
        f"got {len(entries)}: {sorted(entries)!r}."
    )
    assert "index.json" in entries, (
        f"Expected an `index.json` artifact under {DOC_DIR}, got: {sorted(entries)!r}."
    )


def test_index_json_content(trigger_result):
    index_path = os.path.join(DOC_DIR, "index.json")
    assert os.path.isfile(index_path), f"Expected {index_path} to exist."
    with open(index_path, "r", encoding="utf-8") as f:
        try:
            payload = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f"{index_path} is not valid JSON: {exc!s}")
    assert isinstance(payload, dict), (
        f"Expected {index_path} to contain a JSON object, got: {type(payload).__name__}."
    )
    assert payload.get("doc_id") == DOC_ID, (
        f"Expected {index_path} doc_id == {DOC_ID!r}, got: {payload.get('doc_id')!r}."
    )
    assert payload.get("word_count") == EXPECTED_WORD_COUNT, (
        f"Expected {index_path} word_count == {EXPECTED_WORD_COUNT}, "
        f"got: {payload.get('word_count')!r}."
    )
    indexed_at = payload.get("indexed_at")
    assert _parse_iso8601(indexed_at) is not None, (
        f"Expected {index_path} indexed_at to be a valid ISO 8601 timestamp, "
        f"got: {indexed_at!r}."
    )
