import os
import shutil


PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_pip3_available():
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."


def test_hatchet_sdk_importable():
    import importlib.util

    spec = importlib.util.find_spec("hatchet_sdk")
    assert spec is not None, "Python package 'hatchet_sdk' is not installed in the environment."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "Environment variable HATCHET_CLIENT_TOKEN must be set in the task environment."


def test_hatchet_server_url_env_present():
    url = os.environ.get("HATCHET_SERVER_URL")
    assert url, "Environment variable HATCHET_SERVER_URL must be set in the task environment."


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set in the task environment."
