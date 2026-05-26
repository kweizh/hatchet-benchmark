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
        f"Expected the aggregate task's final output to be written to {RESULT_FILE}, "
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


def test_count_is_three():
    with open(RESULT_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert "count" in data, (
        f"{RESULT_FILE} must contain a top-level 'count' key. Got keys: {list(data.keys())}"
    )
    count = data["count"]
    assert isinstance(count, int) and not isinstance(count, bool), (
        f"'count' must be an integer. Got type {type(count).__name__}: {count!r}"
    )
    assert count == 3, (
        f"Expected 'count' to equal 3 (three input URLs from prepare), got {count!r}."
    )


def test_total_length_is_175():
    with open(RESULT_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert "total_length" in data, (
        f"{RESULT_FILE} must contain a top-level 'total_length' key. Got keys: {list(data.keys())}"
    )
    total_length = data["total_length"]
    assert isinstance(total_length, int) and not isinstance(total_length, bool), (
        f"'total_length' must be an integer. Got type {type(total_length).__name__}: {total_length!r}"
    )
    # (len("https://example.com/a") + len("/b") + len("/c")) * 7 = (21 + 2 + 2) * 7 = 175
    expected = 175
    assert total_length == expected, (
        f"Expected 'total_length' to equal {expected} "
        f"((len('https://example.com/a') + len('/b') + len('/c')) * 7 = (21 + 2 + 2) * 7), "
        f"got {total_length!r}."
    )


def test_doc_pipeline_dag_defined():
    src = _read_project_source()
    assert src.strip(), (
        f"No Python source files found under {PROJECT_DIR}. The agent must implement the workflows here."
    )
    pattern = re.compile(
        r"""hatchet\.workflow\s*\(\s*[^)]*name\s*=\s*['"]doc[_-]?pipeline['"]""",
        re.IGNORECASE | re.DOTALL,
    )
    assert pattern.search(src), (
        "Expected to find a Hatchet DAG workflow declared via "
        "`hatchet.workflow(name=\"doc_pipeline\")` "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_prepare_task_defined():
    src = _read_project_source()
    # Look for `def prepare(` near a `@<workflow>.task(...)` decorator OR a `name="prepare"` task.
    has_def = re.search(r"\bdef\s+prepare\s*\(", src) is not None
    has_name = re.search(r"""name\s*=\s*['"]prepare['"]""", src) is not None
    assert has_def or has_name, (
        "Expected to find a task named `prepare` defined on the doc_pipeline DAG workflow "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_scrape_all_task_defined_with_prepare_parent():
    src = _read_project_source()
    pattern = re.compile(
        r"@[A-Za-z_][A-Za-z0-9_]*\.task\s*\([^)]*parents\s*=\s*\[\s*prepare\s*\][^)]*\)\s*\n\s*(?:async\s+)?def\s+scrape_all\s*\(",
        re.DOTALL,
    )
    assert pattern.search(src), (
        "Expected to find a task named `scrape_all` declared with `parents=[prepare]` on a Hatchet DAG workflow "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_aggregate_task_defined_with_scrape_all_parent():
    src = _read_project_source()
    pattern = re.compile(
        r"@[A-Za-z_][A-Za-z0-9_]*\.task\s*\([^)]*parents\s*=\s*\[\s*scrape_all\s*\][^)]*\)\s*\n\s*(?:async\s+)?def\s+aggregate\s*\(",
        re.DOTALL,
    )
    assert pattern.search(src), (
        "Expected to find a task named `aggregate` declared with `parents=[scrape_all]` on a Hatchet DAG workflow "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_scrape_one_child_workflow_defined():
    src = _read_project_source()
    # Accept either a separate hatchet.workflow named scrape_one or a standalone @hatchet.task name="scrape_one".
    workflow_pattern = re.compile(
        r"""hatchet\.workflow\s*\(\s*[^)]*name\s*=\s*['"]scrape[_-]?one['"]""",
        re.IGNORECASE | re.DOTALL,
    )
    task_pattern = re.compile(
        r"""@\s*hatchet\.task\s*\([^)]*name\s*=\s*['"]scrape[_-]?one['"]""",
        re.IGNORECASE | re.DOTALL,
    )
    assert workflow_pattern.search(src) or task_pattern.search(src), (
        "Expected to find a separate child workflow named `scrape_one` (declared either via "
        "`hatchet.workflow(name=\"scrape_one\")` or `@hatchet.task(name=\"scrape_one\")`) "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_scrape_all_uses_aio_run_many_for_child_spawning():
    src = _read_project_source()
    # Must use scrape_one.aio_run_many(...) AND scrape_one.create_bulk_run_item(...)
    aio_run_many = re.search(r"scrape_one\.aio_run_many\s*\(", src)
    bulk_run_item = re.search(r"scrape_one\.create_bulk_run_item\s*\(", src)
    assert aio_run_many, (
        "Expected `scrape_all` to fan out by calling `scrape_one.aio_run_many(...)` "
        f"in the Python source files under {PROJECT_DIR}."
    )
    assert bulk_run_item, (
        "Expected `scrape_all` to construct bulk run inputs via `scrape_one.create_bulk_run_item(...)` "
        f"in the Python source files under {PROJECT_DIR}."
    )


def test_aggregate_reads_scrape_all_via_task_output():
    src = _read_project_source()
    pattern = re.compile(
        r"""ctx\.task_output\s*\(\s*(?:scrape_all|['"]scrape_all['"])""",
    )
    assert pattern.search(src), (
        "Expected the `aggregate` task to read the parent's output via "
        "`ctx.task_output(scrape_all)` (or the string-name form) "
        f"in the Python source files under {PROJECT_DIR}."
    )
