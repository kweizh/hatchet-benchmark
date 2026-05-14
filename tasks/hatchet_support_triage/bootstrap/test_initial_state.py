import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/support-agent"

def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."

def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hatchet_sdk_installed():
    result = subprocess.run(
        ["python3", "-c", "import hatchet_sdk"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "hatchet-sdk is not installed or cannot be imported."
