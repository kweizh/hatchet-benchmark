import os
import shutil
import json
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    package_json = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json), f"package.json not found at {package_json}."


def test_hatchet_sdk_installed():
    sdk_dir = os.path.join(PROJECT_DIR, "node_modules", "@hatchet-dev", "typescript-sdk")
    assert os.path.isdir(sdk_dir), (
        "@hatchet-dev/typescript-sdk is not pre-installed in node_modules."
    )


def test_tsx_available_in_project():
    # tsx should be available either as a local dependency or globally.
    project_tsx = os.path.join(PROJECT_DIR, "node_modules", ".bin", "tsx")
    has_global = shutil.which("tsx") is not None
    assert os.path.isfile(project_tsx) or has_global, (
        "tsx is not available either as a local dependency or globally."
    )


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    assert token.strip() != "", "HATCHET_CLIENT_TOKEN environment variable is not set."


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id.strip() != "", "ZEALT_RUN_ID environment variable is not set."
