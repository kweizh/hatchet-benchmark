import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist."
    )


def test_jj_repo_initialized():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert os.path.isdir(jj_dir), (
        f"Expected {jj_dir} to exist, indicating a jj repository is initialized."
    )


def test_colocated_git_repo_exists():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert os.path.isdir(git_dir), (
        f"Expected {git_dir} to exist, indicating a colocated git repository."
    )


def test_jj_status_runs():
    result = subprocess.run(
        ["jj", "status"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected 'jj status' to succeed inside {PROJECT_DIR}, "
        f"got returncode={result.returncode}, stderr={result.stderr}"
    )


def test_user_name_not_set_to_target_value():
    """user.name must not already be 'Alice Example' before the task starts."""
    result = subprocess.run(
        ["jj", "config", "get", "user.name"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    # jj may return an empty default; either way, it must NOT already be
    # set to the target value.
    assert result.stdout.strip() != "Alice Example", (
        "Expected user.name NOT to be 'Alice Example' initially, but it was."
    )


def test_user_email_not_set_to_target_value():
    """user.email must not already be 'alice@example.com' before the task starts."""
    result = subprocess.run(
        ["jj", "config", "get", "user.email"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() != "alice@example.com", (
        "Expected user.email NOT to be 'alice@example.com' initially, but it was."
    )


def test_config_list_user_has_no_user_keys():
    """`jj config list user` should report no matching keys when nothing is set."""
    result = subprocess.run(
        ["jj", "config", "list", "user"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    combined = (result.stdout + result.stderr).lower()
    assert "no matching config key" in combined, (
        "Expected 'jj config list user' to report 'No matching config key' "
        "initially (no user.name/user.email configured at any scope), got "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
