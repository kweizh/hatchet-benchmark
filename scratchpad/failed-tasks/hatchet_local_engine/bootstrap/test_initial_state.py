import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/hatchet-project"

def test_hatchet_binary_available():
    assert shutil.which("hatchet") is not None, "hatchet binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."
