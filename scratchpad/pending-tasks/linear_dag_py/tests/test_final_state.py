import json
import os
import pathlib
import re

PROJECT_DIR = "/home/user/myproject"
RESULT_PATH = "/tmp/result.json"


def _read_all_python_sources():
    sources = []
    for root, _dirs, files in os.walk(PROJECT_DIR):
        # Skip virtualenvs and caches that the agent might create.
        if any(
            skip in root
            for skip in (
                "/.venv",
                "/venv",
                "/node_modules",
                "/__pycache__",
                "/.git",
            )
        ):
            continue
        for fname in files:
            if fname.endswith(".py"):
                fpath = pathlib.Path(root) / fname
                try:
                    sources.append((str(fpath), fpath.read_text(encoding="utf-8", errors="replace")))
                except OSError:
                    continue
    return sources


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist after the task is run."
    )


def test_hatchet_dag_workflow_file_present():
    sources = _read_all_python_sources()
    assert sources, (
        f"Expected at least one Python source file under {PROJECT_DIR} that defines the Hatchet DAG."
    )

    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, (
        "Expected the ZEALT_RUN_ID environment variable to be available during verification."
    )

    expected_workflow_name = f"linear-dag-{run_id}"

    matching = []
    for fpath, content in sources:
        imports_sdk = ("from hatchet_sdk" in content) or ("import hatchet_sdk" in content)
        has_step1 = "step1_load" in content
        has_step2 = "step2_transform" in content
        has_step3 = "step3_finalize" in content
        ctx_output_uses = len(re.findall(r"ctx\.task_output\s*\(", content))
        if (
            imports_sdk
            and has_step1
            and has_step2
            and has_step3
            and ctx_output_uses >= 2
        ):
            matching.append((fpath, content))

    assert matching, (
        "Expected at least one Python file under "
        f"{PROJECT_DIR} that imports from hatchet_sdk, defines tasks named "
        "step1_load, step2_transform and step3_finalize, and uses ctx.task_output(...) "
        "at least twice."
    )

    workflow_name_found = any(expected_workflow_name in content for _f, content in matching)
    assert workflow_name_found, (
        "Expected the Hatchet workflow to be named "
        f"'{expected_workflow_name}' (containing the ZEALT_RUN_ID suffix) in one of the project's Python sources."
    )


def test_result_file_exists_and_valid_json():
    assert os.path.isfile(RESULT_PATH), (
        f"Expected the result file {RESULT_PATH} to exist after the workflow runs."
    )
    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Expected {RESULT_PATH} to contain valid JSON, but parsing failed: {exc}"
            )
    assert isinstance(data, dict), (
        f"Expected the top-level JSON value in {RESULT_PATH} to be an object."
    )


def test_result_final_value():
    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "final" in data, (
        f"Expected the JSON in {RESULT_PATH} to have a top-level 'final' key, got keys: {list(data.keys())!r}."
    )
    assert data["final"] == "hello world!", (
        f"Expected /tmp/result.json 'final' value to be exactly 'hello world!', got: {data['final']!r}."
    )
