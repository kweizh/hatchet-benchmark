import os
import shutil

def test_python_available():
    assert shutil.which("python") is not None or shutil.which("python3") is not None, "Python binary not found in PATH."

def test_pip_available():
    assert shutil.which("pip") is not None or shutil.which("pip3") is not None, "Pip binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir("/home/user/myproject"), "Project directory /home/user/myproject does not exist."