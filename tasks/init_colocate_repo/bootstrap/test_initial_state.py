import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_jj_binary_runs():
    result = subprocess.run(
        ["jj", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj --version` failed with exit code {result.returncode}: {result.stderr}"
    )
    assert "jj" in result.stdout.lower(), (
        f"Expected 'jj' in `jj --version` output, got: {result.stdout!r}"
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task."
    )


def test_project_dir_is_empty():
    entries = os.listdir(PROJECT_DIR)
    assert entries == [], (
        f"Expected {PROJECT_DIR} to be empty before the task, found entries: {entries}"
    )


def test_jj_not_yet_initialized():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert not os.path.exists(jj_dir), (
        f"Expected {jj_dir} to not exist before the task, but it does."
    )


def test_git_not_yet_initialized():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert not os.path.exists(git_dir), (
        f"Expected {git_dir} to not exist before the task, but it does."
    )
