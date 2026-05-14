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


def test_initial_commit_a_exists():
    ids = _get_change_ids_for_description("Commit A")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit A' initially, got {len(ids)}: {ids}"
    )


def test_initial_commit_b_exists():
    ids = _get_change_ids_for_description("Commit B")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit B' initially, got {len(ids)}: {ids}"
    )


def test_initial_commit_c_exists():
    ids = _get_change_ids_for_description("Commit C")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit C' initially, got {len(ids)}: {ids}"
    )


def test_initial_linear_chain_b_parent_is_a():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Commit B")-',
            "--no-graph",
            "-T",
            'description ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Commit B\")-'` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "Commit A" in result.stdout, (
        f"Expected parent of 'Commit B' to be 'Commit A', got: {result.stdout!r}"
    )


def test_initial_linear_chain_c_parent_is_b():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Commit C")-',
            "--no-graph",
            "-T",
            'description ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Commit C\")-'` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "Commit B" in result.stdout, (
        f"Expected parent of 'Commit C' to be 'Commit B', got: {result.stdout!r}"
    )


def test_initial_file_a_content():
    result = subprocess.run(
        ["jj", "file", "show", "-r", 'description(substring:"Commit C")', "a.txt"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show` for a.txt at Commit C failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "content A", (
        f"Expected a.txt content to be 'content A', got {result.stdout!r}"
    )


def test_initial_file_b_content():
    result = subprocess.run(
        ["jj", "file", "show", "-r", 'description(substring:"Commit C")', "b.txt"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show` for b.txt at Commit C failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "content B", (
        f"Expected b.txt content to be 'content B', got {result.stdout!r}"
    )


def test_initial_file_c_content():
    result = subprocess.run(
        ["jj", "file", "show", "-r", 'description(substring:"Commit C")', "c.txt"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show` for c.txt at Commit C failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "content C", (
        f"Expected c.txt content to be 'content C', got {result.stdout!r}"
    )


def test_initial_working_copy_parent_is_commit_c():
    result = subprocess.run(
        ["jj", "log", "-r", "@-", "--no-graph", "-T", 'description ++ "\\n"'],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r @-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "Commit C" in result.stdout, (
        f"Expected the parent of the working copy to have description 'Commit C', "
        f"got: {result.stdout!r}"
    )
