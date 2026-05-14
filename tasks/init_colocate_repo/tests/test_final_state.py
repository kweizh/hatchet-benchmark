import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def test_jj_directory_exists():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert os.path.isdir(jj_dir), (
        f"Expected {jj_dir} to exist as a directory after `jj git init --colocate`."
    )


def test_git_directory_exists():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert os.path.isdir(git_dir), (
        f"Expected {git_dir} to exist as a directory after `jj git init --colocate`."
    )


def test_jj_status_succeeds():
    result = subprocess.run(
        ["jj", "status"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR} with exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_jj_workspace_root_matches_project_dir():
    result = subprocess.run(
        ["jj", "workspace", "root"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj workspace root` failed in {PROJECT_DIR} with exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    reported_root = os.path.realpath(result.stdout.strip())
    expected_root = os.path.realpath(PROJECT_DIR)
    assert reported_root == expected_root, (
        f"Expected `jj workspace root` to print {expected_root}, got: {reported_root}"
    )
