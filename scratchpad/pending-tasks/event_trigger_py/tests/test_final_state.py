import json
import os
import re
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_DIR = "/home/user/myproject"
OUTPUT_FILE = "/tmp/triggered.json"


@pytest.fixture(scope="module")
def run_id():
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "ZEALT_RUN_ID environment variable is not set."
    return value


@pytest.fixture(scope="module")
def triggered_payload():
    assert os.path.isfile(OUTPUT_FILE), (
        f"Expected output file {OUTPUT_FILE} to exist after running the task, but it does not."
    )
    assert os.path.getsize(OUTPUT_FILE) > 0, (
        f"Output file {OUTPUT_FILE} exists but is empty."
    )
    with open(OUTPUT_FILE, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Output file {OUTPUT_FILE} does not contain valid JSON: {exc}"
            )
    return data


def test_output_file_top_level_shape(triggered_payload):
    assert isinstance(triggered_payload, dict), (
        f"Expected top-level JSON in {OUTPUT_FILE} to be an object, got {type(triggered_payload).__name__}."
    )
    assert "event_payload" in triggered_payload, (
        f"Expected key 'event_payload' in {OUTPUT_FILE}, but got keys: {list(triggered_payload.keys())}."
    )
    assert "received_at" in triggered_payload, (
        f"Expected key 'received_at' in {OUTPUT_FILE}, but got keys: {list(triggered_payload.keys())}."
    )


def test_event_payload_user_id_matches_run_id(triggered_payload, run_id):
    event_payload = triggered_payload.get("event_payload")
    assert isinstance(event_payload, dict), (
        f"Expected 'event_payload' in {OUTPUT_FILE} to be an object, got {type(event_payload).__name__}."
    )
    expected_user_id = f"abc-{run_id}"
    assert event_payload.get("user_id") == expected_user_id, (
        f"Expected event_payload.user_id == {expected_user_id!r} in {OUTPUT_FILE}, "
        f"got {event_payload.get('user_id')!r}."
    )


def test_received_at_is_iso_timestamp(triggered_payload):
    received_at = triggered_payload.get("received_at")
    assert isinstance(received_at, str) and received_at, (
        f"Expected 'received_at' in {OUTPUT_FILE} to be a non-empty string, got {received_at!r}."
    )
    # Allow trailing 'Z' for UTC, which datetime.fromisoformat does not natively accept on older versions.
    normalized = received_at[:-1] + "+00:00" if received_at.endswith("Z") else received_at
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AssertionError(
            f"received_at value {received_at!r} in {OUTPUT_FILE} is not a valid ISO 8601 timestamp: {exc}"
        )


def test_event_trigger_wired_in_source():
    """Verify the project source actually wires the on_events=['user:created'] trigger."""
    project_path = Path(PROJECT_DIR)
    assert project_path.is_dir(), f"Project directory {PROJECT_DIR} does not exist."

    pattern = re.compile(
        r"on_events\s*=\s*\[[^\]]*['\"]user:created['\"][^\]]*\]",
        re.DOTALL,
    )

    matched_file = None
    for py_file in project_path.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pattern.search(text):
            matched_file = py_file
            break

    assert matched_file is not None, (
        "Expected at least one Python source file under "
        f"{PROJECT_DIR} to declare on_events=[..., 'user:created', ...], "
        "but no such declaration was found."
    )
