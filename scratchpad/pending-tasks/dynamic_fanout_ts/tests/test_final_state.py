import json
import os

RESULT_FILE = "/tmp/result.json"
PROJECT_DIR = "/home/user/myproject"
PACKAGE_JSON = os.path.join(PROJECT_DIR, "package.json")

EXPECTED_SQUARES = [1, 4, 9, 16, 25]


def test_result_file_exists():
    assert os.path.isfile(RESULT_FILE), (
        f"Expected output file {RESULT_FILE} to exist after the task runs."
    )


def test_result_file_is_valid_json():
    with open(RESULT_FILE) as f:
        content = f.read()
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"{RESULT_FILE} must contain valid JSON, but parsing failed: {e}; content was: {content!r}"
        )


def test_result_object_has_squares_key():
    with open(RESULT_FILE) as f:
        data = json.load(f)
    assert isinstance(data, dict), (
        f"Top-level JSON in {RESULT_FILE} must be an object, got: {type(data).__name__}"
    )
    assert "squares" in data, (
        f"Expected 'squares' key in {RESULT_FILE}, got keys: {list(data.keys())}"
    )


def test_squares_values_match_expected_order():
    with open(RESULT_FILE) as f:
        data = json.load(f)
    squares = data.get("squares")
    assert isinstance(squares, list), (
        f"'squares' must be a list, got: {type(squares).__name__}"
    )
    # Coerce numeric types and compare
    coerced = []
    for i, v in enumerate(squares):
        assert isinstance(v, (int, float)) and not isinstance(v, bool), (
            f"squares[{i}] must be a number, got: {type(v).__name__} ({v!r})"
        )
        coerced.append(int(v))
    assert coerced == EXPECTED_SQUARES, (
        f"Expected squares == {EXPECTED_SQUARES}, got {coerced} (raw: {squares})."
    )


def test_package_json_declares_real_hatchet_sdk():
    assert os.path.isfile(PACKAGE_JSON), f"{PACKAGE_JSON} must exist."
    with open(PACKAGE_JSON) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    assert "@hatchet-dev/typescript-sdk" in deps, (
        "package.json must declare the real @hatchet-dev/typescript-sdk dependency (no mocks)."
    )


def test_hatchet_sdk_installed_in_node_modules():
    sdk_path = os.path.join(PROJECT_DIR, "node_modules", "@hatchet-dev", "typescript-sdk")
    assert os.path.isdir(sdk_path), (
        f"The real @hatchet-dev/typescript-sdk must be installed under {sdk_path}."
    )
