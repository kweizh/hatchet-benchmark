import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_pnpm_available():
    assert shutil.which("pnpm") is not None, "pnpm binary not found in PATH."


def test_tsx_available():
    # tsx may be invoked via pnpm exec or as a local binary; check both.
    has_tsx = shutil.which("tsx") is not None
    if not has_tsx:
        result = subprocess.run(
            ["pnpm", "exec", "tsx", "--version"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        has_tsx = result.returncode == 0
    assert has_tsx, "tsx is not available (neither in PATH nor via 'pnpm exec tsx')."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    package_json = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json), f"{package_json} does not exist."


def test_hatchet_sdk_installed():
    # The Hatchet TypeScript SDK must be installed under node_modules.
    sdk_dir = os.path.join(PROJECT_DIR, "node_modules", "@hatchet-dev", "typescript-sdk")
    assert os.path.isdir(sdk_dir), (
        f"@hatchet-dev/typescript-sdk is not installed under {sdk_dir}."
    )


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    assert token.strip(), "HATCHET_CLIENT_TOKEN env var must be set for Hatchet Cloud auth."


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id.strip(), "ZEALT_RUN_ID env var must be set for parallel-run isolation."
