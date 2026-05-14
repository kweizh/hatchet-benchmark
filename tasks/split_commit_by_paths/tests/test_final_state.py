import os
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


def _change_ids_for(revset):
    result = _run_jj(
        ["log", "-r", revset, "--no-graph", "-T", 'change_id ++ "\\n"']
    )
    assert result.returncode == 0, (
        f"`jj log -r {revset!r}` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_exactly_one_feature_a_commit():
    """Priority 1: There must be exactly one commit with description 'Feature A'."""
    ids = _change_ids_for('description(substring:"Feature A")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description 'Feature A', "
        f"got {len(ids)}: {ids}"
    )


def test_exactly_one_feature_b_commit():
    """Priority 1: There must be exactly one commit with description 'Feature B'."""
    ids = _change_ids_for('description(substring:"Feature B")')
    assert len(ids) == 1, (
        f"Expected exactly 1 commit with description 'Feature B', "
        f"got {len(ids)}: {ids}"
    )


def test_no_combined_changes_commit_remains():
    """Priority 1: The original 'Combined changes' commit must be gone."""
    ids = _change_ids_for('description(substring:"Combined changes")')
    assert len(ids) == 0, (
        f"Expected no commit with description 'Combined changes' to remain "
        f"after splitting, got {len(ids)}: {ids}"
    )


def test_feature_a_description_exact():
    """Priority 1: The 'Feature A' commit's description must be exactly 'Feature A'."""
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Feature A")',
            "--no-graph",
            "-T",
            "description",
        ]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Feature A", (
        f"Expected exact description 'Feature A', got: {result.stdout!r}"
    )


def test_feature_b_description_exact():
    """Priority 1: The 'Feature B' commit's description must be exactly 'Feature B'."""
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Feature B")',
            "--no-graph",
            "-T",
            "description",
        ]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Feature B", (
        f"Expected exact description 'Feature B', got: {result.stdout!r}"
    )


def test_feature_a_diff_contains_only_feature_a_py():
    """Priority 1: `jj diff -r 'description(substring:"Feature A")'` shows only feature_a.py."""
    result = _run_jj(
        [
            "diff",
            "-r",
            'description(substring:"Feature A")',
            "--summary",
        ]
    )
    assert result.returncode == 0, (
        f"jj diff failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "feature_a.py" in result.stdout, (
        f"Expected diff of 'Feature A' commit to mention feature_a.py, "
        f"got: {result.stdout!r}"
    )
    assert "feature_b.py" not in result.stdout, (
        f"Expected diff of 'Feature A' commit to NOT mention feature_b.py, "
        f"got: {result.stdout!r}"
    )


def test_feature_b_diff_contains_only_feature_b_py():
    """Priority 1: `jj diff -r 'description(substring:"Feature B")'` shows only feature_b.py."""
    result = _run_jj(
        [
            "diff",
            "-r",
            'description(substring:"Feature B")',
            "--summary",
        ]
    )
    assert result.returncode == 0, (
        f"jj diff failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "feature_b.py" in result.stdout, (
        f"Expected diff of 'Feature B' commit to mention feature_b.py, "
        f"got: {result.stdout!r}"
    )
    assert "feature_a.py" not in result.stdout, (
        f"Expected diff of 'Feature B' commit to NOT mention feature_a.py, "
        f"got: {result.stdout!r}"
    )


def test_feature_a_is_parent_of_feature_b():
    """Priority 1: The parent of the 'Feature B' commit must be the 'Feature A' commit."""
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Feature B")-',
            "--no-graph",
            "-T",
            "description",
        ]
    )
    assert result.returncode == 0, (
        f"jj log of parent of 'Feature B' failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Feature A", (
        f"Expected the parent of the 'Feature B' commit to be 'Feature A', "
        f"got: {result.stdout!r}"
    )


def test_feature_a_py_content_unchanged():
    """Priority 3: feature_a.py on disk must still contain its original content."""
    assert os.path.isfile(FEATURE_A), f"Expected file {FEATURE_A} to exist."
    with open(FEATURE_A) as f:
        content = f.read()
    assert content.strip() == 'def a(): return "a"', (
        f"Expected feature_a.py to still contain 'def a(): return \"a\"', "
        f"got: {content!r}"
    )


def test_feature_b_py_content_unchanged():
    """Priority 3: feature_b.py on disk must still contain its original content."""
    assert os.path.isfile(FEATURE_B), f"Expected file {FEATURE_B} to exist."
    with open(FEATURE_B) as f:
        content = f.read()
    assert content.strip() == 'def b(): return "b"', (
        f"Expected feature_b.py to still contain 'def b(): return \"b\"', "
        f"got: {content!r}"
    )


def test_exactly_two_non_root_non_empty_commits():
    """Priority 1: After splitting, exactly two non-root non-empty commits remain."""
    ids = _change_ids_for("~root() & ~empty()")
    assert len(ids) == 2, (
        f"Expected exactly 2 non-root, non-empty commits after splitting "
        f"('Feature A' and 'Feature B'), got {len(ids)}: {ids}"
    )
