import os
import shutil
import subprocess


PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_node_available():
    assert shutil.which("node") is not None, "Node.js binary 'node' not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_tsx_available():
    assert shutil.which("tsx") is not None, "tsx binary not found in PATH."


def test_hatchet_typescript_sdk_installed():
    result = subprocess.run(
        ["npm", "ls", "@hatchet-dev/typescript-sdk", "--depth=0"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert "@hatchet-dev/typescript-sdk" in combined, (
        "Expected '@hatchet-dev/typescript-sdk' to be installed in the project: "
        f"{combined}"
    )


def test_hatchet_client_token_env_present():
    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN environment variable must be set for the task to run."
    )


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable must be set."
