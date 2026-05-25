import json
import os

RESULT_FILE = "/tmp/result.json"
STATE_FILE = "/tmp/agent_state.json"
LOG_FILE = "/home/user/myproject/output.log"


def _load_json(path):
    assert os.path.isfile(path), f"Expected file {path} to exist but it does not."
    with open(path, "r") as f:
        text = f.read()
    try:
        return json.loads(text)
    except Exception as e:
        raise AssertionError(
            f"Expected file {path} to contain valid JSON, but parsing failed: {e}. "
            f"File contents (truncated): {text[:500]!r}"
        )


def test_result_file_final_step_is_five():
    data = _load_json(RESULT_FILE)
    assert isinstance(data, dict), (
        f"Expected /tmp/result.json to contain a JSON object, got: {type(data).__name__}"
    )
    assert "final_step" in data, (
        f"Expected /tmp/result.json to contain top-level field 'final_step'. Got keys: {list(data.keys())}"
    )
    assert data["final_step"] == 5, (
        f"Expected /tmp/result.json final_step == 5, got: {data['final_step']!r}"
    )


def test_result_file_history_length_is_five():
    data = _load_json(RESULT_FILE)
    assert "history_length" in data, (
        f"Expected /tmp/result.json to contain top-level field 'history_length'. Got keys: {list(data.keys())}"
    )
    assert data["history_length"] == 5, (
        f"Expected /tmp/result.json history_length == 5, got: {data['history_length']!r}"
    )


def test_state_file_step_is_five():
    state = _load_json(STATE_FILE)
    assert isinstance(state, dict), (
        f"Expected /tmp/agent_state.json to contain a JSON object, got: {type(state).__name__}"
    )
    assert "step" in state, (
        f"Expected /tmp/agent_state.json to contain top-level field 'step'. Got keys: {list(state.keys())}"
    )
    assert state["step"] == 5, (
        f"Expected /tmp/agent_state.json step == 5, got: {state['step']!r}"
    )


def test_state_file_history_has_five_entries_in_order():
    state = _load_json(STATE_FILE)
    assert "history" in state, (
        f"Expected /tmp/agent_state.json to contain top-level field 'history'. Got keys: {list(state.keys())}"
    )
    history = state["history"]
    assert isinstance(history, list), (
        f"Expected /tmp/agent_state.json 'history' to be a list, got: {type(history).__name__}"
    )
    assert len(history) == 5, (
        f"Expected /tmp/agent_state.json history length == 5, got: {len(history)} entries: {history!r}"
    )
    for i, entry in enumerate(history):
        expected_thought = f"iter {i + 1}"
        assert isinstance(entry, dict), (
            f"Expected history[{i}] to be a JSON object, got: {type(entry).__name__} ({entry!r})"
        )
        assert "thought" in entry, (
            f"Expected history[{i}] to contain field 'thought'. Got: {entry!r}"
        )
        assert entry["thought"] == expected_thought, (
            f"Expected history[{i}].thought == {expected_thought!r}, got: {entry['thought']!r}"
        )


def test_runner_log_file_exists_and_non_empty():
    assert os.path.isfile(LOG_FILE), (
        f"Expected runner log file at {LOG_FILE} to exist."
    )
    size = os.path.getsize(LOG_FILE)
    assert size > 0, (
        f"Expected runner log file at {LOG_FILE} to be non-empty, but its size is {size} bytes."
    )
