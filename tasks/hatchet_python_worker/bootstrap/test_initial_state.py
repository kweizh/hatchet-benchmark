import os
import shutil

PROJECT_DIR = "/home/user/hatchet-worker"

def test_python_available():
    assert shutil.which("python") is not None or shutil.which("python3") is not None, "python binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."
