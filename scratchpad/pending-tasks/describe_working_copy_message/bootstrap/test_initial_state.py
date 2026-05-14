import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def test_jj_binary_available():
    assert shutil.which("jj") is not None, \
        "jj binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), \
        f"Project directory {PROJECT_DIR} does not exist."


def test_jj_repo_initialized():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert os.path.isdir(jj_dir), \
        f"Expected colocated jj repo: {jj_dir} not found."


def test_colocated_git_dir_exists():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert os.path.isdir(git_dir), \
        f"Expected colocated git directory {git_dir} not found (repo should be colocated)."


def test_readme_exists_in_workdir():
    readme = os.path.join(PROJECT_DIR, "README.md")
    assert os.path.isfile(readme), \
        f"Expected uncommitted README.md at {readme} in the working copy."


def test_user_name_configured():
    result = subprocess.run(
        ["jj", "config", "get", "user.name"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj config get user.name' failed: {result.stderr}"
    assert result.stdout.strip() != "", \
        "user.name is not configured for jj."


def test_user_email_configured():
    result = subprocess.run(
        ["jj", "config", "get", "user.email"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj config get user.email' failed: {result.stderr}"
    assert result.stdout.strip() != "", \
        "user.email is not configured for jj."


def test_working_copy_description_is_empty():
    result = subprocess.run(
        ["jj", "log", "-r", "@", "--no-graph", "-T", "description"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj log -r @ -T description' failed: {result.stderr}"
    assert result.stdout.strip() == "", \
        f"Expected empty description on @, got: {result.stdout!r}"


def test_working_copy_contains_readme_change():
    # The working copy commit @ should already include the uncommitted
    # changes to README.md, because jj auto-snapshots the working copy.
    result = subprocess.run(
        ["jj", "diff", "-r", "@", "--summary"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj diff -r @ --summary' failed: {result.stderr}"
    assert "README.md" in result.stdout, \
        f"Expected README.md in working-copy diff summary, got: {result.stdout!r}"


def test_working_copy_is_not_empty():
    result = subprocess.run(
        ["jj", "log", "-r", "@", "--no-graph", "-T", "empty"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj log -r @ -T empty' failed: {result.stderr}"
    assert result.stdout.strip() == "false", \
        f"Expected working copy @ to be non-empty (empty=false), got: {result.stdout!r}"
