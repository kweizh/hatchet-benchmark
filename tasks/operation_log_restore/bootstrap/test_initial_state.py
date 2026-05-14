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
        f"Expected user.name to be configured, got rc={result_name.returncode} "
        f"stdout={result_name.stdout!r} stderr={result_name.stderr!r}"
    )
    result_email = subprocess.run(
        ["jj", "config", "get", "user.email"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_email.returncode == 0 and result_email.stdout.strip() != "", (
        f"Expected user.email to be configured, got rc={result_email.returncode} "
        f"stdout={result_email.stdout!r} stderr={result_email.stderr!r}"
    )


def _get_change_ids_for_description(substring):
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            f'description(substring:"{substring}")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for description '{substring}' failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def test_initial_stage1_exists():
    ids = _get_change_ids_for_description("Stage 1")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Stage 1' in initial state, "
        f"got {len(ids)}: {ids}"
    )


def test_initial_stage2_absent():
    ids = _get_change_ids_for_description("Stage 2")
    assert len(ids) == 0, (
        f"Expected NO commit with description 'Stage 2' in initial state (Stage 2 should "
        f"have been abandoned and only recoverable via the operation log), got {len(ids)}: {ids}"
    )


def test_initial_stage3_exists():
    ids = _get_change_ids_for_description("Stage 3")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Stage 3' in initial state, "
        f"got {len(ids)}: {ids}"
    )


def test_initial_extra1_exists():
    ids = _get_change_ids_for_description("extra1")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'extra1' in initial state, "
        f"got {len(ids)}: {ids}"
    )


def test_initial_extra2_exists():
    ids = _get_change_ids_for_description("extra2")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'extra2' in initial state, "
        f"got {len(ids)}: {ids}"
    )


def test_initial_file1_exists_on_disk():
    file1 = os.path.join(PROJECT_DIR, "file1.txt")
    assert os.path.isfile(file1), f"Expected {file1} to exist on disk in initial state."
    with open(file1) as f:
        content = f.read().strip()
    assert content == "content A", (
        f"Expected initial content of file1.txt to be 'content A', got {content!r}"
    )


def test_initial_file2_absent_on_disk():
    file2 = os.path.join(PROJECT_DIR, "file2.txt")
    assert not os.path.exists(file2), (
        f"Expected {file2} to NOT exist in initial state (Stage 2 was abandoned), "
        f"but the file is present."
    )


def test_initial_file3_exists_on_disk():
    file3 = os.path.join(PROJECT_DIR, "file3.txt")
    assert os.path.isfile(file3), f"Expected {file3} to exist on disk in initial state."
    with open(file3) as f:
        content = f.read().strip()
    assert content == "content C", (
        f"Expected initial content of file3.txt to be 'content C', got {content!r}"
    )


def test_initial_op_log_contains_stage2_commit_operation():
    """The op log must retain the original `jj commit -m \"Stage 2\"` operation so the
    agent can discover and restore to it."""
    result = subprocess.run(
        ["jj", "op", "log", "--no-graph"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj op log` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    # jj records args with shell-quoting; accept either single or double quotes.
    assert ("commit -m 'Stage 2'" in result.stdout
            or 'commit -m "Stage 2"' in result.stdout), (
        f"Expected `jj op log` output to contain the original "
        f"`commit -m 'Stage 2'` (or double-quoted) operation args, got: {result.stdout!r}"
    )


def test_initial_op_log_contains_abandon_operation():
    """The op log must show that Stage 2 was abandoned at some point in the history."""
    result = subprocess.run(
        ["jj", "op", "log", "--no-graph"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj op log` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "abandon" in result.stdout.lower(), (
        f"Expected `jj op log` output to contain an 'abandon' operation, "
        f"got: {result.stdout!r}"
    )
