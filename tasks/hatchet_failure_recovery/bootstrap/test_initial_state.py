import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/project"

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hatchet_sdk_installed():
    result = subprocess.run(["python3", "-c", "import hatchet_sdk"], capture_output=True)
    assert result.returncode == 0, "hatchet-sdk is not installed in the Python environment."
