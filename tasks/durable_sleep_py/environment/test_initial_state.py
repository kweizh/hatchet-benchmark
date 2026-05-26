import importlib
import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_hatchet_sdk_importable():
    spec = importlib.util.find_spec("hatchet_sdk")
    assert spec is not None, (
        "hatchet_sdk Python package is not installed or not importable; "
        "the Hatchet Python SDK must be available before the task starts."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist; "
        "it must be present before the executor begins the task."
    )


def test_hatchet_client_token_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable is not set; "
        "the Hatchet Cloud client token is required to authenticate."
    )
