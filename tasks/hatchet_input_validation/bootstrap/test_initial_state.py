import os
import shutil
import pytest

PROJECT_DIR = "/home/user/app"

def test_python_binary_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hatchet_sdk_installed():
    try:
        import hatchet_sdk
    except ImportError:
        pytest.fail("hatchet_sdk is not installed in the environment.")

def test_pydantic_installed():
    try:
        import pydantic
    except ImportError:
        pytest.fail("pydantic is not installed in the environment.")
