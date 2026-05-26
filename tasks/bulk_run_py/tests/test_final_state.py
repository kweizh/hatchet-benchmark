import json
import os

import pytest

RESULTS_PATH = "/tmp/results.json"
EXPECTED_NS = list(range(1, 11))


@pytest.fixture(scope="module")
def results():
    assert os.path.isfile(RESULTS_PATH), (
        f"Expected results file {RESULTS_PATH} to exist after the runner finishes."
    )
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"{RESULTS_PATH} is not valid JSON: {e!r}"
            )
    return data


def test_results_file_is_list_of_ten(results):
    assert isinstance(results, list), (
        f"Expected the top-level JSON value in {RESULTS_PATH} to be a list, "
        f"got {type(results).__name__}."
    )
    assert len(results) == 10, (
        f"Expected exactly 10 entries in {RESULTS_PATH}, got {len(results)}."
    )


def test_each_entry_has_correct_schema(results):
    for i, entry in enumerate(results):
        assert isinstance(entry, dict), (
            f"Entry at index {i} is not a JSON object: {entry!r}"
        )
        assert set(entry.keys()) == {"n", "result"}, (
            f"Entry at index {i} must have exactly the keys 'n' and 'result'; "
            f"got keys {sorted(entry.keys())!r}."
        )
        n_val = entry["n"]
        r_val = entry["result"]
        assert isinstance(n_val, int) and not isinstance(n_val, bool), (
            f"Entry at index {i} field 'n' must be an int, got {type(n_val).__name__}: {n_val!r}"
        )
        assert isinstance(r_val, int) and not isinstance(r_val, bool), (
            f"Entry at index {i} field 'result' must be an int, got {type(r_val).__name__}: {r_val!r}"
        )


def test_n_values_cover_one_to_ten(results):
    ns = [entry["n"] for entry in results]
    assert sorted(ns) == EXPECTED_NS, (
        f"Expected the set of 'n' values to be {EXPECTED_NS} with no duplicates, "
        f"got {sorted(ns)!r}."
    )


def test_result_equals_double_n(results):
    for entry in results:
        n_val = entry["n"]
        r_val = entry["result"]
        assert r_val == n_val * 2, (
            f"Expected result == n * 2 for entry {entry!r}; "
            f"got n={n_val}, result={r_val}, expected result={n_val * 2}."
        )


def test_entries_ordered_by_n_ascending(results):
    for i, entry in enumerate(results):
        assert entry["n"] == i + 1, (
            f"Entries must be ordered by 'n' ascending. Expected entry at index "
            f"{i} to have n={i + 1}, got n={entry['n']}."
        )
