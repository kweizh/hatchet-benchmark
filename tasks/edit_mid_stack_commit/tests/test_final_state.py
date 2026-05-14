import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"

# Ensure jj does not invoke a pager in non-interactive subprocess runs.
ENV = {**os.environ, "JJ_PAGER": "cat", "PAGER": "cat"}


def _jj(*args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=ENV,
    )


def test_b_extra_file_exists_in_workdir():
    """The working-copy tip must contain the new b_extra.txt."""
    p = os.path.join(PROJECT_DIR, "b_extra.txt")
    assert os.path.isfile(p), \
        f"Expected new file {p} to exist in the working-copy tip."


def test_b_extra_file_has_expected_content():
    """b_extra.txt must contain exactly 'extra line for B'."""
    p = os.path.join(PROJECT_DIR, "b_extra.txt")
    with open(p) as f:
        content = f.read()
    assert "extra line for B" in content, \
        f"Expected b_extra.txt to contain 'extra line for B', got: {content!r}"


@pytest.mark.parametrize("fname", ["a.txt", "b.txt", "c.txt", "d.txt"])
def test_workdir_tip_contains_all_stack_files(fname):
    """After returning to the tip, all stack files must be materialised on disk."""
    p = os.path.join(PROJECT_DIR, fname)
    assert os.path.isfile(p), \
        f"Expected {p} to exist in the working-copy tip after rebase."


def test_descendants_of_commit_b_include_c_and_d():
    """`description(substring:'Commit B')::` must yield Commit B, C, and D."""
    r = _jj(
        "log", "-r", 'description(substring:"Commit B")::',
        "--no-graph", "-T", 'description.first_line() ++ "\n"',
    )
    assert r.returncode == 0, f"'jj log' failed: {r.stderr}"
    for desc in ("Commit B", "Commit C", "Commit D"):
        assert desc in r.stdout, \
            f"Expected {desc!r} in B::-descendants log, got: {r.stdout!r}"


def test_commit_b_diff_references_b_extra_txt():
    """`jj diff -r 'description(substring:\"Commit B\")'` must mention b_extra.txt."""
    r = _jj("--no-pager", "diff", "-r", 'description(substring:"Commit B")')
    assert r.returncode == 0, f"'jj diff' failed: {r.stderr}"
    assert "b_extra.txt" in r.stdout, \
        f"Expected b_extra.txt to appear in Commit B's diff, got: {r.stdout!r}"


def test_commit_b_diff_includes_added_line_text():
    """The diff for Commit B must include the added line 'extra line for B'."""
    r = _jj("--no-pager", "diff", "-r", 'description(substring:"Commit B")')
    assert r.returncode == 0, f"'jj diff' failed: {r.stderr}"
    assert "extra line for B" in r.stdout, \
        f"Expected the added text 'extra line for B' in Commit B diff, got: {r.stdout!r}"


def test_commit_b_summary_includes_both_b_and_b_extra():
    """Commit B's diff summary must include both b.txt (original) and b_extra.txt (new)."""
    r = _jj(
        "--no-pager", "diff", "-r", 'description(substring:"Commit B")', "--summary",
    )
    assert r.returncode == 0, f"'jj diff --summary' failed: {r.stderr}"
    assert "b.txt" in r.stdout, \
        f"Expected b.txt in Commit B summary, got: {r.stdout!r}"
    assert "b_extra.txt" in r.stdout, \
        f"Expected b_extra.txt in Commit B summary, got: {r.stdout!r}"


def test_commit_c_and_d_still_present_after_rebase():
    """Commit C and Commit D must still be present after the auto-rebase."""
    for desc, fname in (("Commit C", "c.txt"), ("Commit D", "d.txt")):
        log = _jj(
            "log", "-r", f'description(substring:"{desc}")',
            "--no-graph", "-T", 'description.first_line() ++ "\n"',
        )
        assert log.returncode == 0, f"'jj log' for {desc!r} failed: {log.stderr}"
        assert desc in log.stdout, \
            f"Expected {desc!r} to still be present after rebase, got: {log.stdout!r}"

        diff = _jj(
            "--no-pager", "diff", "-r", f'description(substring:"{desc}")', "--summary",
        )
        assert diff.returncode == 0, \
            f"'jj diff --summary' for {desc!r} failed: {diff.stderr}"
        assert fname in diff.stdout, \
            f"Expected {desc!r} to still introduce {fname!r}, got: {diff.stdout!r}"


def test_commit_b_parent_is_commit_a():
    """The rewritten Commit B's parent must still be Commit A."""
    r = _jj(
        "log", "-r", 'description(substring:"Commit B")-',
        "--no-graph", "-T", 'description.first_line()',
    )
    assert r.returncode == 0, f"'jj log' for parent of B failed: {r.stderr}"
    assert "Commit A" in r.stdout, \
        f"Expected parent of Commit B to be Commit A, got: {r.stdout!r}"


def test_commit_d_is_descendant_of_commit_b():
    """Commit D must appear in the descendants set of Commit B (stack ordering preserved)."""
    r = _jj(
        "log", "-r",
        'description(substring:"Commit B")::',
        "--no-graph", "-T", 'description.first_line() ++ "\n"',
    )
    assert r.returncode == 0, f"'jj log' failed: {r.stderr}"
    descs = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    assert "Commit D" in descs, \
        f"Expected Commit D in descendants of Commit B, got: {descs!r}"
    assert "Commit C" in descs, \
        f"Expected Commit C in descendants of Commit B, got: {descs!r}"
