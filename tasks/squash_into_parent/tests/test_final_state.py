import os
import subprocess

PROJECT_DIR = "/home/user/myrepo"
APP_PY = os.path.join(PROJECT_DIR, "app.py")


def _run_jj(args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_parent_commit_description_is_initial_implementation():
    """Priority 1: Use jj CLI to inspect the description of @-."""
    result = _run_jj(["log", "-r", "@-", "--no-graph", "-T", "description"])
    assert result.returncode == 0, (
        f"`jj log -r '@-'` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Initial implementation", (
        f"Expected description of @- to be 'Initial implementation' after squash, "
        f"got: {result.stdout!r}"
    )


def test_exactly_one_non_root_non_empty_commit():
    """Priority 1: After `jj squash`, only one real commit should remain."""
    result = _run_jj(
        ["log", "-r", "~root() & ~empty()", "--no-graph", "-T", "change_id ++ \"\\n\""]
    )
    assert result.returncode == 0, (
        f"`jj log` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) == 1, (
        f"Expected exactly 1 non-root, non-empty commit after squash, "
        f"got {len(change_ids)}: {change_ids}"
    )


def test_working_copy_is_empty_after_squash():
    """Priority 1: After `jj squash`, @ should be a new empty commit on top."""
    result = _run_jj(["log", "-r", "@", "--no-graph", "-T", "empty"])
    assert result.returncode == 0, (
        f"`jj log -r '@'` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "true", (
        f"Expected working copy @ to be empty after squash, got empty={result.stdout!r}"
    )


def test_working_copy_description_is_empty_after_squash():
    """The new working copy commit should have no description."""
    result = _run_jj(["log", "-r", "@", "--no-graph", "-T", "description"])
    assert result.returncode == 0, (
        f"`jj log -r '@'` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "", (
        f"Expected working copy @ description to be empty after squash, "
        f"got: {result.stdout!r}"
    )


def test_app_py_final_content():
    """Priority 3: app.py on disk should contain the combined final content."""
    assert os.path.isfile(APP_PY), f"Expected file {APP_PY} to exist."
    with open(APP_PY) as f:
        content = f.read()
    assert content == "def main(): return 0\n", (
        f"Expected app.py content to be exactly 'def main(): return 0\\n', "
        f"got: {content!r}"
    )


def test_parent_commit_contains_final_app_py():
    """Priority 1: `jj diff -r '@-'` should show app.py being added with the final content."""
    result = _run_jj(["diff", "-r", "@-"])
    assert result.returncode == 0, (
        f"`jj diff -r '@-'` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    diff = result.stdout
    assert "app.py" in diff, (
        f"Expected `jj diff -r '@-'` to mention app.py, got: {diff!r}"
    )
    assert "def main(): return 0" in diff, (
        f"Expected `jj diff -r '@-'` to show the squashed-in final content "
        f"'def main(): return 0', got: {diff!r}"
    )
    assert "def main(): pass" not in diff, (
        f"Expected the old content 'def main(): pass' to be gone from the parent "
        f"commit diff after squashing, got: {diff!r}"
    )


def test_parent_commit_is_not_empty():
    """The remaining non-root commit must actually contain changes."""
    result = _run_jj(["log", "-r", "@-", "--no-graph", "-T", "empty"])
    assert result.returncode == 0, (
        f"`jj log -r '@-'` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "false", (
        f"Expected @- to be non-empty (it contains app.py), got empty={result.stdout!r}"
    )
