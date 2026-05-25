import json
import os
import shutil

PROJECT_DIR = "/home/user/myproject"
PACKAGE_JSON = os.path.join(PROJECT_DIR, "package.json")
NODE_MODULES = os.path.join(PROJECT_DIR, "node_modules")


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    assert os.path.isfile(PACKAGE_JSON), f"package.json not found at {PACKAGE_JSON}."


def test_package_json_declares_hatchet_sdk():
    with open(PACKAGE_JSON) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@hatchet-dev/typescript-sdk" in deps, (
        "package.json must declare @hatchet-dev/typescript-sdk as a dependency."
    )


def test_package_json_declares_tsx():
    with open(PACKAGE_JSON) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "tsx" in deps, "package.json must declare tsx as a dependency for running TypeScript files."


def test_node_modules_installed():
    assert os.path.isdir(NODE_MODULES), (
        f"node_modules directory not found at {NODE_MODULES}; dependencies must be installed."
    )
    sdk_path = os.path.join(NODE_MODULES, "@hatchet-dev", "typescript-sdk")
    assert os.path.isdir(sdk_path), (
        f"@hatchet-dev/typescript-sdk is not installed under {sdk_path}."
    )


def test_hatchet_client_token_env_var_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable must be set for Hatchet Cloud access."


def test_zealt_run_id_env_var_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for parallel-run safety."
