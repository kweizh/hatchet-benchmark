import os
import importlib.util


PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hatchet_sdk_importable():
    spec = importlib.util.find_spec("hatchet_sdk")
    assert spec is not None, "hatchet_sdk Python package is not installed."


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token is not None and token != "", (
        "HATCHET_CLIENT_TOKEN environment variable must be set to a non-empty value."
    )
