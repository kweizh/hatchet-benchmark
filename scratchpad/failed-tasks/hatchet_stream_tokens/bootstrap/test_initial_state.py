import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/app"

def test_hatchet_binary_available():
    assert shutil.which("hatchet") is not None, "hatchet binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_python_sdk_installed():
    result = subprocess.run(["pip3", "show", "hatchet-sdk"], capture_output=True, text=True)
    assert result.returncode == 0, "hatchet-sdk is not installed."
