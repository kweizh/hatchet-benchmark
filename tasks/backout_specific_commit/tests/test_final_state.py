import os
import subprocess

PROJECT_DIR = "/home/user/myrepo"
APP_PY = os.path.join(PROJECT_DIR, "app.py")
README = os.path.join(PROJECT_DIR, "README.md")


def _run_jj(args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_app_py_buggy_line_removed():
    """app.py on disk must be back to the original 'print(\"hello\")' content."""
    assert os.path.isfile(APP_PY), f"Expected file {APP_PY} to exist."
    with open(APP_PY) as f:
        content = f.read()
    assert content == 'print("hello")\n', (
        f"Expected app.py to contain exactly 'print(\"hello\")\\n' after revert, "
        f"got: {content!r}"
    )
    assert "BUG: do not commit" not in content, (
        f"Expected the buggy line to be gone from app.py, got: {content!r}"
    )


def test_readme_preserved():
    """README.md must still exist with the same content as initially."""
    assert os.path.isfile(README), f"Expected file {README} to exist."
    with open(README) as f:
        content = f.read()
    assert content == "Project docs\n", (
        f"Expected README.md to be preserved as 'Project docs\\n', got: {content!r}"
    )


def test_three_original_commits_still_present():
    """Priority 1: All three original commits must still exist in the repo."""
    result = _run_jj(
        ["log", "-r", "~root()", "--no-graph", "-T", "description ++ \"\\n\""]
    )
    assert result.returncode == 0, (
        f"`jj log` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    descriptions = result.stdout
    for desc in ("Initial app", "Bad change", "Add documentation"):
        assert desc in descriptions, (
            f"Expected commit description {desc!r} to still be present after revert, "
            f"got: {descriptions!r}"
        )


def test_bad_change_commit_still_exists_exactly_once():
    """Priority 1: The original 'Bad change' commit must still be intact (not abandoned)."""
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Bad change")',
            "--no-graph",
            "-T",
            "change_id ++ \"\\n\"",
        ]
    )
    assert result.returncode == 0, (
        f"`jj log` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) >= 1, (
        f"Expected the original 'Bad change' commit to still exist, "
        f"got change_ids={change_ids!r}"
    )


def test_revert_commit_present_in_ancestry():
    """Priority 1: A new non-empty commit must exist in @'s ancestry in addition
    to the three original commits.

    We count the total non-empty, non-root commits reachable from @ and require
    that there are MORE than 3 — i.e. a 4th commit (the revert) was added.
    """
    result = _run_jj(
        [
            "log",
            "-r",
            "::@ & ~root() & ~empty()",
            "--no-graph",
            "-T",
            "change_id ++ \"\\n\"",
        ]
    )
    assert result.returncode == 0, (
        f"`jj log` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) >= 4, (
        f"Expected at least 4 non-empty commits in the ancestry of @ "
        f"(3 originals + at least 1 revert commit), got {len(change_ids)}: "
        f"{change_ids!r}"
    )


def test_revert_commit_inverts_bad_change():
    """Priority 1: The cumulative diff from the 'Add documentation' commit to @
    must remove the buggy line, demonstrating that a revert was applied.
    """
    result = _run_jj(
        [
            "diff",
            "--from",
            'description(substring:"Add documentation")',
            "--to",
            "@",
        ]
    )
    assert result.returncode == 0, (
        f"`jj diff` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    diff = result.stdout
    # The cumulative diff from 'Add documentation' to @ should remove the buggy line.
    assert "BUG: do not commit" in diff, (
        f"Expected the revert diff (from 'Add documentation' to @) to mention "
        f"the removed line containing 'BUG: do not commit', got: {diff!r}"
    )


def test_working_copy_app_py_via_jj_file_show():
    """Priority 1: Use `jj file show` to verify the tracked content of app.py at @."""
    result = _run_jj(["file", "show", "-r", "@", "app.py"])
    assert result.returncode == 0, (
        f"`jj file show -r @ app.py` failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout == 'print("hello")\n', (
        f"Expected `jj file show -r @ app.py` to output 'print(\"hello\")\\n', "
        f"got: {result.stdout!r}"
    )


def test_working_copy_readme_via_jj_file_show():
    """Priority 1: Use `jj file show` to verify README.md at @ is preserved."""
    result = _run_jj(["file", "show", "-r", "@", "README.md"])
    assert result.returncode == 0, (
        f"`jj file show -r @ README.md` failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout == "Project docs\n", (
        f"Expected `jj file show -r @ README.md` to output 'Project docs\\n', "
        f"got: {result.stdout!r}"
    )
