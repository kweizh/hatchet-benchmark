import os
import shutil
import subprocess


PROJECT_DIR = "/home/user/myproject"


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_tsx_binary_available():
    assert shutil.which("tsx") is not None, (
        "tsx binary not found in PATH; it should be installed globally to run TypeScript files."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hatchet_client_token_env_var_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token is not None and token.strip() != "", (
        "HATCHET_CLIENT_TOKEN environment variable must be set to authenticate with Hatchet Cloud."
    )


def test_zealt_run_id_env_var_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None and run_id.strip() != "", (
        "ZEALT_RUN_ID environment variable must be set so tasks can isolate per-run resources."
    )


def test_node_can_resolve_hatchet_sdk():
    # The Hatchet TypeScript SDK should be globally installed so the agent can
    # use it from the project without re-fetching from the network in offline
    # environments. We verify that Node can resolve the package by name.
    result = subprocess.run(
        ["node", "-e", "require.resolve('@hatchet-dev/typescript-sdk')"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "Node could not resolve '@hatchet-dev/typescript-sdk'. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
