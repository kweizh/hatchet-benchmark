import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/agent_loop"

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_python_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."

def test_pip_available():
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."
