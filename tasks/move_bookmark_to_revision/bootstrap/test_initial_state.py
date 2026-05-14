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


def _commit_count_for(description):
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            f'description(substring:"{description}")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for description {description!r} failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_commit_1_exists():
    ids = _commit_count_for("Commit 1")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit 1' in the initial state, got {len(ids)}: {ids}"
    )


def test_commit_2_exists():
    ids = _commit_count_for("Commit 2")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit 2' in the initial state, got {len(ids)}: {ids}"
    )


def test_commit_3_exists():
    ids = _commit_count_for("Commit 3")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit 3' in the initial state, got {len(ids)}: {ids}"
    )


def test_linear_history_commit2_parent_of_commit3():
    # The parent of Commit 3 must have description Commit 2.
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Commit 3")-',
            "--no-graph",
            "-T",
            "description.first_line()",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Commit 3\")-'` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Commit 2", (
        f"Expected the parent of 'Commit 3' to have description 'Commit 2', got: {result.stdout!r}"
    )


def test_linear_history_commit1_parent_of_commit2():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Commit 2")-',
            "--no-graph",
            "-T",
            "description.first_line()",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Commit 2\")-'` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Commit 1", (
        f"Expected the parent of 'Commit 2' to have description 'Commit 1', got: {result.stdout!r}"
    )


def test_working_copy_is_empty_child_of_commit3():
    # The working copy @ must be a new empty commit whose parent has description "Commit 3".
    result_parent_desc = subprocess.run(
        ["jj", "log", "-r", "@-", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_parent_desc.returncode == 0, (
        f"`jj log -r @-` failed: stdout={result_parent_desc.stdout!r}, stderr={result_parent_desc.stderr!r}"
    )
    assert result_parent_desc.stdout.strip() == "Commit 3", (
        f"Expected the parent of the working copy to have description 'Commit 3', got: {result_parent_desc.stdout!r}"
    )


def test_feature_bookmark_exists():
    result = subprocess.run(
        ["jj", "bookmark", "list", "feature"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj bookmark list feature` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "feature" in result.stdout, (
        f"Expected the local bookmark 'feature' to exist initially, got: {result.stdout!r}"
    )


def test_feature_bookmark_points_to_commit_2_initially():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            "feature",
            "--no-graph",
            "-T",
            "description.first_line()",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r feature` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Commit 2", (
        f"Expected the 'feature' bookmark to initially point to the commit with description 'Commit 2', got: {result.stdout!r}"
    )
