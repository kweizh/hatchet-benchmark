import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"
LOG_FILE = os.path.join(PROJECT_DIR, "log_output.txt")


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_jj_binary_runs():
    result = subprocess.run(
        ["jj", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj --version` failed with exit code {result.returncode}: {result.stderr}"
    )
    assert "jj" in result.stdout.lower(), (
        f"Expected 'jj' in `jj --version` output, got: {result.stdout!r}"
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task."
    )


def test_jj_repo_initialized():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert os.path.isdir(jj_dir), (
        f"Expected {jj_dir} to exist (colocated jj repo not initialized)."
    )


def test_git_repo_initialized():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert os.path.isdir(git_dir), (
        f"Expected {git_dir} to exist (colocated git repo not initialized)."
    )


def test_jj_status_succeeds():
    result = subprocess.run(
        ["jj", "status"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def _commit_descriptions():
    """Return the list of first-line descriptions of all non-root commits."""
    result = subprocess.run(
        [
            "jj",
            "log",
            "--no-graph",
            "-r",
            "all() ~ root()",
            "-T",
            'description.first_line() ++ "\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` failed in {PROJECT_DIR}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return [line for line in result.stdout.splitlines()]


def test_initial_commit_present():
    descriptions = _commit_descriptions()
    assert "Initial commit" in descriptions, (
        f"Expected a commit with description 'Initial commit'. Got: {descriptions!r}"
    )


def test_feature_b_commit_present():
    descriptions = _commit_descriptions()
    assert "Add feature B" in descriptions, (
        f"Expected a commit with description 'Add feature B'. Got: {descriptions!r}"
    )


def test_bug_c_commit_present():
    descriptions = _commit_descriptions()
    assert "Fix bug C" in descriptions, (
        f"Expected a commit with description 'Fix bug C'. Got: {descriptions!r}"
    )


def test_three_seeded_files_exist():
    for filename in ("file1.txt", "file2.txt", "file3.txt"):
        path = os.path.join(PROJECT_DIR, filename)
        assert os.path.isfile(path), (
            f"Expected seeded file {path} to exist in the initial repository state."
        )


def test_log_output_file_absent():
    assert not os.path.exists(LOG_FILE), (
        f"Expected {LOG_FILE} to not exist before the task, but it does."
    )
