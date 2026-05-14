import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"
REMOTE_DIR = "/home/user/remote.git"
BOOKMARK = "my-feature"


def _run_jj(args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def _run_git_remote(args):
    return subprocess.run(
        ["git", "--git-dir", REMOTE_DIR, *args],
        capture_output=True,
        text=True,
    )


def _local_bookmark_commit_id():
    result = _run_jj(["log", "-r", BOOKMARK, "--no-graph", "-T", "commit_id"])
    assert result.returncode == 0, (
        f"`jj log -r {BOOKMARK}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return result.stdout.strip()


def test_local_bookmark_my_feature_exists():
    """Priority 1: Use jj CLI to verify the local bookmark exists."""
    result = _run_jj(["bookmark", "list", BOOKMARK])
    assert result.returncode == 0, (
        f"`jj bookmark list {BOOKMARK}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert f"{BOOKMARK}:" in result.stdout, (
        f"Expected local bookmark '{BOOKMARK}' to exist, got: stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}"
    )


def test_local_bookmark_points_to_second_commit():
    """Priority 1: Use jj CLI to verify the bookmark resolves to the 'Second' commit."""
    result = _run_jj(["log", "-r", BOOKMARK, "--no-graph", "-T", "description.first_line()"])
    assert result.returncode == 0, (
        f"`jj log -r {BOOKMARK}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Second", (
        f"Expected local bookmark '{BOOKMARK}' to point to the commit with description 'Second', "
        f"got: {result.stdout!r}"
    )


def test_remote_has_my_feature_ref():
    """Priority 1: Use git on the bare remote to verify the ref was pushed."""
    result = _run_git_remote(["show-ref", f"refs/heads/{BOOKMARK}"])
    assert result.returncode == 0, (
        f"Expected the remote bare repo {REMOTE_DIR} to have ref 'refs/heads/{BOOKMARK}', "
        f"but `git show-ref` exited with rc={result.returncode}, "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert f"refs/heads/{BOOKMARK}" in result.stdout, (
        f"Expected 'refs/heads/{BOOKMARK}' in `git show-ref` output, got: {result.stdout!r}"
    )


def test_remote_my_feature_matches_local_commit_id():
    """Priority 1: Verify the remote ref points to the same commit ID as the local bookmark."""
    local_commit_id = _local_bookmark_commit_id()
    assert len(local_commit_id) == 40, (
        f"Expected local bookmark commit id to be a 40-char SHA, got: {local_commit_id!r}"
    )
    result = _run_git_remote(["rev-parse", f"refs/heads/{BOOKMARK}"])
    assert result.returncode == 0, (
        f"`git rev-parse refs/heads/{BOOKMARK}` against {REMOTE_DIR} failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    remote_commit_id = result.stdout.strip()
    assert remote_commit_id == local_commit_id, (
        f"Expected remote ref 'refs/heads/{BOOKMARK}' (={remote_commit_id!r}) to point to the "
        f"same commit as the local bookmark (={local_commit_id!r})."
    )


def test_remote_my_feature_has_second_description():
    """Priority 1: Verify the remote commit's subject is 'Second'."""
    result = _run_git_remote(
        ["log", "--format=%s", "-n", "1", f"refs/heads/{BOOKMARK}"]
    )
    assert result.returncode == 0, (
        f"`git log refs/heads/{BOOKMARK}` against {REMOTE_DIR} failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Second", (
        f"Expected the tip of remote 'refs/heads/{BOOKMARK}' to have subject 'Second', "
        f"got: {result.stdout!r}"
    )


def _commit_lines_for(description):
    result = _run_jj(
        [
            "log",
            "-r",
            f'description(substring:"{description}")',
            "--no-graph",
            "-T",
            'description.first_line() ++ "\\n"',
        ]
    )
    assert result.returncode == 0, (
        f"`jj log` for description {description!r} failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_first_commit_unmodified():
    lines = _commit_lines_for("First")
    assert len(lines) == 1 and lines[0] == "First", (
        f"Expected exactly one commit with description 'First' after the push, got: {lines}"
    )


def test_second_commit_unmodified():
    lines = _commit_lines_for("Second")
    assert len(lines) == 1 and lines[0] == "Second", (
        f"Expected exactly one commit with description 'Second' after the push, got: {lines}"
    )
