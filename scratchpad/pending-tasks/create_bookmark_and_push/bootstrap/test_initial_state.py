import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"
REMOTE_DIR = "/home/user/remote.git"


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_git_binary_available():
    assert shutil.which("git") is not None, "git binary not found in PATH."


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


def test_remote_bare_repo_exists():
    assert os.path.isdir(REMOTE_DIR), (
        f"Expected the bare git remote directory {REMOTE_DIR} to exist."
    )
    result = subprocess.run(
        ["git", "--git-dir", REMOTE_DIR, "rev-parse", "--is-bare-repository"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and result.stdout.strip() == "true", (
        f"Expected {REMOTE_DIR} to be a bare git repository, got rc={result.returncode}, "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_remote_has_no_my_feature_ref():
    result = subprocess.run(
        ["git", "--git-dir", REMOTE_DIR, "show-ref", "refs/heads/my-feature"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0 and result.stdout.strip() == "", (
        f"Expected the remote bare repo {REMOTE_DIR} to have NO ref 'refs/heads/my-feature' "
        f"initially, got rc={result.returncode}, stdout={result.stdout!r}"
    )


def test_origin_remote_configured():
    result = subprocess.run(
        ["jj", "git", "remote", "list"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj git remote list` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "origin" in result.stdout, (
        f"Expected 'origin' remote to be configured in {PROJECT_DIR}, got: {result.stdout!r}"
    )
    # The origin URL must reference the local bare repo path.
    assert REMOTE_DIR in result.stdout, (
        f"Expected origin remote URL to reference {REMOTE_DIR}, got: {result.stdout!r}"
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
    for key in ("user.name", "user.email"):
        result = subprocess.run(
            ["jj", "config", "get", key],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0 and result.stdout.strip() != "", (
            f"Expected {key} to be configured, got rc={result.returncode} "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )


def _commit_lines_for(description):
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            f'description(substring:"{description}")',
            "--no-graph",
            "-T",
            'description.first_line() ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for description {description!r} failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_first_commit_exists():
    lines = _commit_lines_for("First")
    assert len(lines) == 1 and lines[0] == "First", (
        f"Expected exactly one commit with description 'First', got: {lines}"
    )


def test_second_commit_exists():
    lines = _commit_lines_for("Second")
    assert len(lines) == 1 and lines[0] == "Second", (
        f"Expected exactly one commit with description 'Second', got: {lines}"
    )


def test_first_txt_in_first_commit():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"First")',
            "--no-graph",
            "--summary",
            "-T",
            '""',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log --summary` for 'First' failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "first.txt" in result.stdout, (
        f"Expected commit 'First' to introduce file 'first.txt', got summary: {result.stdout!r}"
    )


def test_second_txt_in_second_commit():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Second")',
            "--no-graph",
            "--summary",
            "-T",
            '""',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log --summary` for 'Second' failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "second.txt" in result.stdout, (
        f"Expected commit 'Second' to introduce file 'second.txt', got summary: {result.stdout!r}"
    )


def test_linear_history_first_parent_of_second():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Second")-',
            "--no-graph",
            "-T",
            "description.first_line()",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Second\")-'` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "First", (
        f"Expected the parent of 'Second' to have description 'First', got: {result.stdout!r}"
    )


def test_working_copy_parent_is_second():
    result = subprocess.run(
        ["jj", "log", "-r", "@-", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r @-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Second", (
        f"Expected the parent of the working copy to have description 'Second', got: {result.stdout!r}"
    )


def test_working_copy_is_empty():
    # The working copy `@` must currently have no description and no file changes.
    result_desc = subprocess.run(
        ["jj", "log", "-r", "@", "--no-graph", "-T", "description"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_desc.returncode == 0, (
        f"`jj log -r @` failed: stdout={result_desc.stdout!r}, stderr={result_desc.stderr!r}"
    )
    assert result_desc.stdout.strip() == "", (
        f"Expected the working copy to have an empty description, got: {result_desc.stdout!r}"
    )


def test_no_my_feature_bookmark_locally():
    result = subprocess.run(
        ["jj", "bookmark", "list", "my-feature"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    # Either the command exits non-zero, or it succeeds with no 'my-feature:' entry.
    combined = (result.stdout or "") + (result.stderr or "")
    assert "my-feature:" not in result.stdout, (
        f"Expected no local bookmark 'my-feature' initially, got: stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}"
    )
