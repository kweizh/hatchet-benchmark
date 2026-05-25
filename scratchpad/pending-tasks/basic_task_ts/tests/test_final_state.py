import json
import os


PROJECT_DIR = "/home/user/myproject"
RESULT_FILE = "/tmp/result.json"


def test_result_file_exists():
    assert os.path.isfile(RESULT_FILE), (
        f"Expected result file {RESULT_FILE} to exist after running the worker and runner."
    )


def test_result_file_is_valid_json():
    with open(RESULT_FILE, "r") as f:
        content = f.read()
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Result file {RESULT_FILE} does not contain valid JSON: {exc}. Raw content: {content!r}"
        )


def test_result_contains_expected_greeting():
    with open(RESULT_FILE, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Expected the result JSON to be an object, got {type(data).__name__}: {data!r}"
    )
    greeting = data.get("greeting")
    assert greeting == "Hello, World!", (
        f"Expected result['greeting'] == 'Hello, World!', got {greeting!r}. Full result: {data!r}"
    )


def test_project_files_exist():
    for name in ("worker.ts", "runner.ts", "package.json", "tsconfig.json"):
        path = os.path.join(PROJECT_DIR, name)
        assert os.path.isfile(path), (
            f"Expected project file {path} to exist after task completion."
        )


def test_package_json_declares_hatchet_sdk_dependency():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path, "r") as f:
        pkg = json.load(f)
    deps = {}
    for key in ("dependencies", "devDependencies"):
        section = pkg.get(key) or {}
        if isinstance(section, dict):
            deps.update(section)
    assert "@hatchet-dev/typescript-sdk" in deps, (
        "Expected package.json to declare a dependency on '@hatchet-dev/typescript-sdk'. "
        f"Found dependencies: {sorted(deps.keys())}"
    )
