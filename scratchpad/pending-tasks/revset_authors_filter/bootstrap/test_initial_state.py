import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def _run_jj(*args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def _change_ids_for_revset(revset):
    result = _run_jj("log", "-r", revset, "--no-graph", "-T", 'change_id ++ "\\n"')
    assert result.returncode == 0, (
        f"`jj log -r {revset!r}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


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
    result = _run_jj("status")
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR}: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_alice_has_three_commits():
    ids = _change_ids_for_revset('author(substring:"Alice")')
    assert len(ids) == 3, (
        f"Expected exactly 3 commits authored by Alice in the initial state, got {len(ids)}: {ids}"
    )


def test_bob_has_one_commit():
    ids = _change_ids_for_revset('author(substring:"Bob")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit authored by Bob in the initial state, got {len(ids)}: {ids}"
    )


def test_charlie_has_one_commit():
    ids = _change_ids_for_revset('author(substring:"Charlie")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit authored by Charlie in the initial state, got {len(ids)}: {ids}"
    )


def test_initial_alice_fix_matches_count_is_two():
    ids = _change_ids_for_revset(
        'author(substring:"Alice") & description(substring:"fix")'
    )
    assert len(ids) == 2, (
        f"Expected exactly 2 commits authored by Alice with 'fix' in description, got {len(ids)}: {ids}"
    )


def test_fix_login_bug_commit_exists():
    ids = _change_ids_for_revset('description(substring:"fix login bug")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description containing 'fix login bug', got {len(ids)}: {ids}"
    )


def test_fix_database_commit_exists():
    ids = _change_ids_for_revset('description(substring:"fix database")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description containing 'fix database', got {len(ids)}: {ids}"
    )


def test_add_feature_x_commit_exists():
    ids = _change_ids_for_revset('description(substring:"add feature X")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description containing 'add feature X', got {len(ids)}: {ids}"
    )


def test_fix_typo_commit_exists():
    ids = _change_ids_for_revset('description(substring:"fix typo in README")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description containing 'fix typo in README', got {len(ids)}: {ids}"
    )


def test_add_tests_commit_exists():
    ids = _change_ids_for_revset('description(substring:"add tests")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description containing 'add tests', got {len(ids)}: {ids}"
    )


def test_expected_files_exist_in_repo():
    # Each of the five user commits introduced a distinct file. The files
    # should be present in the working copy because the working-copy commit
    # is a child of the last user commit and inherits the tree.
    for fname in ("file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"):
        path = os.path.join(PROJECT_DIR, fname)
        assert os.path.isfile(path), (
            f"Expected pre-existing file {path} to be present in the working copy."
        )
