import json
import os
import re

import pytest

PROJECT_DIR = "/home/user/myproject"
RESULT_FILE = "/tmp/result.json"


def _read_project_source() -> str:
    """Concatenate all .py source files under the project directory."""
    chunks = []
    for root, _dirs, files in os.walk(PROJECT_DIR):
        # Skip virtualenv / cache directories
        parts = set(root.split(os.sep))
        if parts & {".venv", "venv", "__pycache__", ".git", "node_modules", "site-packages"}:
            continue
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        chunks.append(f"# === {fpath} ===\n" + fh.read())
                except Exception:
                    pass
    return "\n".join(chunks)


def test_result_file_exists():
    assert os.path.isfile(RESULT_FILE), (
        f"Expected the parent workflow's final output to be written to {RESULT_FILE}, "
        f"but the file does not exist."
    )


def test_result_file_is_valid_json_object():
    with open(RESULT_FILE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
    except Exception as e:
        raise AssertionError(
            f"{RESULT_FILE} is not valid JSON: {e}. Contents: {raw!r}"
        )
    assert isinstance(data, dict), (
        f"{RESULT_FILE} must be a JSON object (dict). Got type {type(data).__name__}: {data!r}"
    )


def test_result_has_squares_key():
    with open(RESULT_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert "squares" in data, (
        f"{RESULT_FILE} must contain a top-level 'squares' key. Got keys: {list(data.keys())}"
    )
    squares = data["squares"]
    assert isinstance(squares, list), (
        f"The 'squares' value in {RESULT_FILE} must be a list. Got type {type(squares).__name__}: {squares!r}"
    )
    assert all(isinstance(x, int) for x in squares), (
        f"All elements of 'squares' must be integers. Got: {squares!r}"
    )


def test_squares_values_are_correct():
    with open(RESULT_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    squares = data.get("squares")
    expected = [1, 4, 9, 16, 25]
    assert squares == expected, (
        f"Expected 'squares' to equal {expected} (squares of input [1,2,3,4,5] in original order), "
        f"got {squares!r}."
    )


def test_child_workflow_square_item_defined():
    src = _read_project_source()
    assert src.strip(), (
        f"No Python source files found under {PROJECT_DIR}. The agent must implement the workflows here."
    )
    # Look for a Hatchet task/workflow definition named "square_item"
    pattern = re.compile(
        r"""name\s*=\s*['"]square[_-]?item['"]""",
        re.IGNORECASE,
    )
    assert pattern.search(src), (
        "Expected to find a Hatchet task/workflow named 'square_item' "
        "(e.g., @hatchet.task(name=\"square_item\") or @hatchet.workflow(name=\"square_item\")) "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_parent_workflow_process_batch_defined():
    src = _read_project_source()
    pattern = re.compile(
        r"""name\s*=\s*['"]process[_-]?batch['"]""",
        re.IGNORECASE,
    )
    assert pattern.search(src), (
        "Expected to find a Hatchet task/workflow named 'process_batch' "
        "(e.g., @hatchet.task(name=\"process_batch\") or @hatchet.workflow(name=\"process_batch\")) "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_parent_invokes_child_via_hatchet_spawning():
    """
    The parent must spawn child workflow runs at runtime rather than computing
    item*item inline. We look for evidence that the parent's source references
    the child workflow object and invokes it through one of Hatchet's run APIs.
    """
    src = _read_project_source()

    # Look for any invocation pattern characteristic of Hatchet child spawning.
    invocation_patterns = [
        r"\.aio_run\s*\(",
        r"\.aio_run_many\s*\(",
        r"\.run_many\s*\(",
        r"\.run_many_no_wait\s*\(",
        r"\.run_no_wait\s*\(",
        r"\.run\s*\(",
        r"create_bulk_run_item\s*\(",
        r"spawn_workflow\s*\(",
        r"spawnWorkflow\s*\(",
        r"spawn_child\s*\(",
    ]
    found_invocation = any(re.search(p, src) for p in invocation_patterns)
    assert found_invocation, (
        "Expected the parent workflow's source to invoke the child workflow via a Hatchet "
        "run API (e.g., .run(...), .aio_run(...), .aio_run_many(...), .run_many(...), "
        "or create_bulk_run_item(...)). None of these invocation patterns were found "
        f"in the Python source files under {PROJECT_DIR}."
    )

    # Ensure the parent does not just compute the square inline using item*item or item**2.
    # Allow such expressions only inside the child task. We do a simple structural check:
    # the source should reference the child workflow's name from within the project.
    references_child = re.search(r"square[_-]?item", src, re.IGNORECASE)
    assert references_child, (
        "Expected the parent workflow's code to reference the 'square_item' child workflow "
        f"in the Python source files under {PROJECT_DIR}."
    )
