import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"
FEATURE_A = os.path.join(PROJECT_DIR, "feature_a.py")
FEATURE_B = os.path.join(PROJECT_DIR, "feature_b.py")


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


def test_feature_a_file_exists_with_initial_content():
    assert os.path.isfile(FEATURE_A), f"Expected file {FEATURE_A} to exist."
    with open(FEATURE_A) as f:
        content = f.read()
    assert content.strip() == 'def a(): return "a"', (
        f"Expected feature_a.py to contain 'def a(): return \"a\"', got: {content!r}"
    )


def test_feature_b_file_exists_with_initial_content():
    assert os.path.isfile(FEATURE_B), f"Expected file {FEATURE_B} to exist."
    with open(FEATURE_B) as f:
        content = f.read()
    assert content.strip() == 'def b(): return "b"', (
        f"Expected feature_b.py to contain 'def b(): return \"b\"', got: {content!r}"
    )


def test_combined_changes_commit_exists():
    """The repository must start with a commit whose description is 'Combined changes'."""
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Combined changes")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) == 1, (
        f"Expected exactly 1 'Combined changes' commit initially, "
        f"got {len(change_ids)}: {change_ids}"
    )


def test_combined_changes_commit_contains_both_files():
    """The initial 'Combined changes' commit must touch both feature_a.py and feature_b.py."""
    result = _run_jj(
        [
            "diff",
            "-r",
            'description(substring:"Combined changes")',
            "--summary",
        ]
    )
    assert result.returncode == 0, (
        f"jj diff failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "feature_a.py" in result.stdout, (
        f"Expected diff of 'Combined changes' commit to mention feature_a.py, "
        f"got: {result.stdout!r}"
    )
    assert "feature_b.py" in result.stdout, (
        f"Expected diff of 'Combined changes' commit to mention feature_b.py, "
        f"got: {result.stdout!r}"
    )


def test_working_copy_is_empty_child_of_combined_changes():
    """`@` must be empty and its parent must be the 'Combined changes' commit."""
    empty = _run_jj(["log", "-r", "@", "--no-graph", "-T", "empty"])
    assert empty.returncode == 0, (
        f"jj log -r @ failed: stdout={empty.stdout!r} stderr={empty.stderr!r}"
    )
    assert empty.stdout.strip() == "true", (
        f"Expected working copy @ to be empty initially, got empty={empty.stdout!r}"
    )

    parent_desc = _run_jj(["log", "-r", "@-", "--no-graph", "-T", "description"])
    assert parent_desc.returncode == 0, (
        f"jj log -r @- failed: stdout={parent_desc.stdout!r} stderr={parent_desc.stderr!r}"
    )
    assert parent_desc.stdout.strip() == "Combined changes", (
        f"Expected parent of @ to have description 'Combined changes', "
        f"got: {parent_desc.stdout!r}"
    )


def test_exactly_one_non_root_non_empty_commit_initially():
    """Initially there is exactly one non-root non-empty commit: 'Combined changes'."""
    result = _run_jj(
        [
            "log",
            "-r",
            "~root() & ~empty()",
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) == 1, (
        f"Expected exactly 1 non-root, non-empty commit initially "
        f"(the 'Combined changes' commit), got {len(change_ids)}: {change_ids}"
    )
