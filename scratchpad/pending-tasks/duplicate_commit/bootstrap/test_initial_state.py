import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_jj_repo_initialized():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert os.path.isdir(jj_dir), f"Expected jj repository directory {jj_dir} to exist."


def test_git_colocated():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert os.path.isdir(git_dir), (
        f"Expected colocated git directory {git_dir} to exist (repo should be a colocated jj/git repo)."
    )


def test_jj_status_runs():
    result = subprocess.run(
        ["jj", "status"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR}: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_user_identity_configured():
    result_name = subprocess.run(
        ["jj", "config", "get", "user.name"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_name.returncode == 0 and result_name.stdout.strip() != "", (
        f"Expected user.name to be configured, got rc={result_name.returncode} stdout={result_name.stdout!r} stderr={result_name.stderr!r}"
    )
    result_email = subprocess.run(
        ["jj", "config", "get", "user.email"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_email.returncode == 0 and result_email.stdout.strip() != "", (
        f"Expected user.email to be configured, got rc={result_email.returncode} stdout={result_email.stdout!r} stderr={result_email.stderr!r}"
    )


def test_exactly_one_feature_a_commit_initially():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Feature A")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) == 1, (
        f"Expected exactly one commit with description 'Feature A' in the initial state, got {len(change_ids)}: {change_ids}"
    )


def test_initial_feature_a_file_content():
    result = subprocess.run(
        [
            "jj",
            "file",
            "show",
            "-r",
            'description(substring:"Feature A")',
            "feature_a.txt",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show` failed for feature_a.txt: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "feature A content", (
        f"Expected feature_a.txt content to be 'feature A content', got {result.stdout!r}"
    )


def test_working_copy_is_empty_child_of_feature_a():
    # The working copy @ should be a new empty commit on top of the Feature A commit.
    # Verify @ has no changed files and its parent has description "Feature A".
    result_parent_desc = subprocess.run(
        ["jj", "log", "-r", "@-", "--no-graph", "-T", "description"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_parent_desc.returncode == 0, (
        f"`jj log -r @-` failed: stdout={result_parent_desc.stdout!r}, stderr={result_parent_desc.stderr!r}"
    )
    assert "Feature A" in result_parent_desc.stdout, (
        f"Expected the parent of the working copy to have description 'Feature A', got: {result_parent_desc.stdout!r}"
    )
