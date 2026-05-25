import json
import os

import pytest


RESULT_FILE = "/tmp/result.json"


@pytest.fixture(scope="module")
def result_payload():
    assert os.path.isfile(RESULT_FILE), (
        f"Expected the agent to write the final merge output to {RESULT_FILE}, "
        "but the file does not exist."
    )
    with open(RESULT_FILE, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            pytest.fail(
                f"{RESULT_FILE} is not valid JSON: {exc!r}"
            )
    return data


def test_result_file_is_json_object(result_payload):
    assert isinstance(result_payload, dict), (
        f"Expected {RESULT_FILE} to contain a JSON object, got: "
        f"{type(result_payload).__name__}"
    )


def test_result_contains_sum_field(result_payload):
    assert "sum" in result_payload, (
        f"Expected key 'sum' in {RESULT_FILE}, found keys: "
        f"{list(result_payload.keys())}"
    )


def test_result_sum_equals_thirty_five(result_payload):
    value = result_payload.get("sum")
    # Accept both ints and floats that are numerically equal to 35.
    assert isinstance(value, (int, float)) and int(value) == 35, (
        f"Expected the 'sum' field in {RESULT_FILE} to equal 35 "
        f"(computed as (10*2) + (10+5)), got: {value!r}"
    )
