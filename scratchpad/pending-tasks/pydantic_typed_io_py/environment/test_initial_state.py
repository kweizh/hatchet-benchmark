import os
import shutil
import importlib

PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_pip3_available():
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."


def test_hatchet_sdk_importable():
    spec = importlib.util.find_spec("hatchet_sdk")
    assert spec is not None, "hatchet_sdk Python package is not installed/importable."


def test_pydantic_importable():
    spec = importlib.util.find_spec("pydantic")
    assert spec is not None, "pydantic Python package is not installed/importable."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."


def test_hatchet_server_url_env_set():
    url = os.environ.get("HATCHET_SERVER_URL")
    assert url, "HATCHET_SERVER_URL environment variable is not set."


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
