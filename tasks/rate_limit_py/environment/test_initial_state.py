import importlib
import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    spec = importlib.util.find_spec("hatchet_sdk")
    assert spec is not None, (
        "hatchet_sdk Python package is not importable. The 'hatchet-sdk' package "
        "must be installed in the task environment."
    )


def test_python3_available():
    assert shutil.which("python3") is not None, (
        "python3 binary not found in PATH; it is required to run the Hatchet worker."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected the project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    assert token.strip() != "", (
        "HATCHET_CLIENT_TOKEN environment variable must be set so the worker and "
        "client can authenticate against Hatchet Cloud."
    )


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id.strip() != "", (
        "ZEALT_RUN_ID environment variable must be set so the rate-limit key can be "
        "made unique across concurrent trials."
    )
