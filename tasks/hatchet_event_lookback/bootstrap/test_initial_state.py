import os
import shutil

PROJECT_DIR = "/home/user/project"

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_python_available():
    assert shutil.which("python3") is not None, "python3 is not available in PATH."
