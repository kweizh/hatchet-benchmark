import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"


def _run_jj(args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_repo_is_colocated_jj_repo():
    assert os.path.isdir(os.path.join(PROJECT_DIR, ".jj")), (
        f"Expected a .jj directory at {PROJECT_DIR}/.jj (colocated jj repo)."
    )
    assert os.path.isdir(os.path.join(PROJECT_DIR, ".git")), (
        f"Expected a .git directory at {PROJECT_DIR}/.git (colocated jj repo)."
    )


def test_user_identity_configured():
    name = _run_jj(["config", "get", "user.name"])
    email = _run_jj(["config", "get", "user.email"])
    assert name.returncode == 0 and name.stdout.strip(), (
        f"user.name is not configured: stdout={name.stdout!r} stderr={name.stderr!r}"
    )
    assert email.returncode == 0 and email.stdout.strip(), (
        f"user.email is not configured: stdout={email.stdout!r} stderr={email.stderr!r}"
    )


def test_app_py_exists_with_working_copy_content():
    app_path = os.path.join(PROJECT_DIR, "app.py")
    assert os.path.isfile(app_path), f"Expected file {app_path} to exist."
    with open(app_path) as f:
        content = f.read()
    assert content.strip() == "def main(): return 0", (
        f"Expected working-copy app.py to contain 'def main(): return 0', got: {content!r}"
    )


def test_parent_commit_description_is_initial_implementation():
    result = _run_jj(
        ["log", "-r", "@-", "--no-graph", "-T", "description"]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Initial implementation", (
        f"Expected parent commit description 'Initial implementation', "
        f"got: {result.stdout!r}"
    )


def test_working_copy_description_is_empty():
    result = _run_jj(
        ["log", "-r", "@", "--no-graph", "-T", "description"]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "", (
        f"Expected working-copy description to be empty, got: {result.stdout!r}"
    )


def test_working_copy_is_not_empty_initially():
    result = _run_jj(
        ["log", "-r", "@", "--no-graph", "-T", "empty"]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "false", (
        f"Expected working copy @ to be non-empty (modifies app.py), "
        f"got empty={result.stdout!r}"
    )


def test_exactly_two_non_root_commits_initially():
    result = _run_jj(
        ["log", "-r", "~root()", "--no-graph", "-T", "change_id ++ \"\\n\""]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) == 2, (
        f"Expected exactly 2 non-root commits initially (parent + working copy), "
        f"got {len(change_ids)}: {change_ids}"
    )
