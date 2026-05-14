import os
import shutil
import pytest

PROJECT_DIR = "/home/user/myproject"

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hatchet_sdk_installed():
    import importlib.util
    assert importlib.util.find_spec("hatchet_sdk") is not None, "hatchet-sdk is not installed in the Python environment."
