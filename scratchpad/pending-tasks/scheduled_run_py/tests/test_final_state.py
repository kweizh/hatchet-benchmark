import json
import os
from datetime import datetime, timedelta, timezone

import pytest

RESULT_FILE = "/tmp/scheduled_result.json"


@pytest.fixture(scope="module")
def result_payload():
    assert os.path.isfile(RESULT_FILE), (
        f"Expected scheduled-run output file at {RESULT_FILE}, but it does not exist."
    )
    with open(RESULT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f"{RESULT_FILE} is not valid JSON: {exc!r}")
    assert isinstance(data, dict), (
        f"Expected {RESULT_FILE} to contain a JSON object, got {type(data).__name__}."
    )
    return data


def test_result_has_input_name_world(result_payload):
    assert "input" in result_payload, (
        f"Expected key 'input' in {RESULT_FILE}, got keys: {list(result_payload)}"
    )
    input_value = result_payload["input"]
    assert isinstance(input_value, dict), (
        f"Expected 'input' to be a JSON object, got {type(input_value).__name__}."
    )
    assert input_value.get("name") == "world", (
        f"Expected input.name == 'world' in {RESULT_FILE}, got: {input_value!r}"
    )


def test_result_has_valid_iso_fired_at(result_payload):
    assert "fired_at" in result_payload, (
        f"Expected key 'fired_at' in {RESULT_FILE}, got keys: {list(result_payload)}"
    )
    fired_at_raw = result_payload["fired_at"]
    assert isinstance(fired_at_raw, str) and fired_at_raw, (
        f"Expected 'fired_at' to be a non-empty string, got: {fired_at_raw!r}"
    )
    normalized = fired_at_raw.replace("Z", "+00:00")
    try:
        fired_at = datetime.fromisoformat(normalized)
    except ValueError as exc:
        pytest.fail(
            f"fired_at value {fired_at_raw!r} is not a valid ISO 8601 timestamp: {exc!r}"
        )

    if fired_at.tzinfo is None:
        fired_at = fired_at.replace(tzinfo=timezone.utc)
    fired_at_utc = fired_at.astimezone(timezone.utc)

    now_utc = datetime.now(tz=timezone.utc)
    assert fired_at_utc <= now_utc + timedelta(minutes=5), (
        f"fired_at {fired_at_utc.isoformat()} is unexpectedly in the future "
        f"compared to current time {now_utc.isoformat()}."
    )
    assert fired_at_utc >= now_utc - timedelta(hours=1), (
        f"fired_at {fired_at_utc.isoformat()} is older than 1 hour relative to "
        f"verifier time {now_utc.isoformat()}; expected a recent scheduled run."
    )
