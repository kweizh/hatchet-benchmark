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


def test_app_py_initial_content_has_bug():
    """Before revert, app.py contains the buggy line on top of the original print."""
    app_path = os.path.join(PROJECT_DIR, "app.py")
    assert os.path.isfile(app_path), f"Expected file {app_path} to exist."
    with open(app_path) as f:
        content = f.read()
    assert content == 'print("hello")\nprint("BUG: do not commit")\n', (
        f"Expected initial app.py to contain the buggy two-line content, got: {content!r}"
    )


def test_readme_initial_content():
    """README.md from the 'Add documentation' commit should already exist."""
    readme_path = os.path.join(PROJECT_DIR, "README.md")
    assert os.path.isfile(readme_path), f"Expected file {readme_path} to exist."
    with open(readme_path) as f:
        content = f.read()
    assert content == "Project docs\n", (
        f"Expected README.md to contain 'Project docs\\n', got: {content!r}"
    )


def test_three_original_commits_present():
    """The three named commits should already exist in the repo history."""
    result = _run_jj(
        ["log", "-r", "~root()", "--no-graph", "-T", "description ++ \"\\n\""]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    output = result.stdout
    for desc in ("Initial app", "Bad change", "Add documentation"):
        assert desc in output, (
            f"Expected commit description {desc!r} to be present in jj log output, "
            f"got: {output!r}"
        )


def test_working_copy_is_empty_initially():
    """The working copy @ should be an empty commit on top of 'Add documentation'."""
    empty = _run_jj(["log", "-r", "@", "--no-graph", "-T", "empty"])
    assert empty.returncode == 0, (
        f"jj log -r '@' failed: stdout={empty.stdout!r} stderr={empty.stderr!r}"
    )
    assert empty.stdout.strip() == "true", (
        f"Expected working copy @ to be empty initially, got empty={empty.stdout!r}"
    )


def test_working_copy_parent_is_add_documentation():
    """@- should be the 'Add documentation' commit."""
    result = _run_jj(["log", "-r", "@-", "--no-graph", "-T", "description"])
    assert result.returncode == 0, (
        f"jj log -r '@-' failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Add documentation", (
        f"Expected @- description to be 'Add documentation', got: {result.stdout!r}"
    )


def test_jj_revert_command_available():
    """The 'jj revert' subcommand must be available in this jj version (>= 0.38)."""
    result = subprocess.run(
        ["jj", "revert", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj revert --help` failed (is jj >= 0.38?): "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
