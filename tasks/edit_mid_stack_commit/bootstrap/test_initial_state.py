import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def _jj(*args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_jj_binary_available():
    assert shutil.which("jj") is not None, \
        "jj binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), \
        f"Project directory {PROJECT_DIR} does not exist."


def test_jj_repo_initialized():
    jj_dir = os.path.join(PROJECT_DIR, ".jj")
    assert os.path.isdir(jj_dir), \
        f"Expected colocated jj repo directory {jj_dir} not found."


def test_colocated_git_dir_exists():
    git_dir = os.path.join(PROJECT_DIR, ".git")
    assert os.path.isdir(git_dir), \
        f"Expected colocated .git directory {git_dir} not found."


def test_user_name_configured():
    r = _jj("config", "get", "user.name")
    assert r.returncode == 0, \
        f"'jj config get user.name' failed: {r.stderr}"
    assert r.stdout.strip() != "", \
        "user.name is not configured for jj."


def test_user_email_configured():
    r = _jj("config", "get", "user.email")
    assert r.returncode == 0, \
        f"'jj config get user.email' failed: {r.stderr}"
    assert r.stdout.strip() != "", \
        "user.email is not configured for jj."


@pytest.mark.parametrize("desc,fname", [
    ("Commit A", "a.txt"),
    ("Commit B", "b.txt"),
    ("Commit C", "c.txt"),
    ("Commit D", "d.txt"),
])
def test_commit_exists_and_contains_expected_file(desc, fname):
    """Each of Commit A/B/C/D must exist and introduce its own file."""
    log = _jj(
        "log", "-r", f'description(substring:"{desc}")',
        "--no-graph", "-T", 'description.first_line() ++ "\n"',
    )
    assert log.returncode == 0, \
        f"'jj log' for {desc!r} failed: {log.stderr}"
    assert desc in log.stdout, \
        f"Expected commit description {desc!r} to be present, got: {log.stdout!r}"

    diff = _jj(
        "diff", "-r", f'description(substring:"{desc}")', "--summary",
    )
    assert diff.returncode == 0, \
        f"'jj diff --summary' for {desc!r} failed: {diff.stderr}"
    assert fname in diff.stdout, \
        f"Expected {fname!r} to be introduced by {desc!r}, got: {diff.stdout!r}"


def test_stack_has_exactly_four_described_commits():
    """The stack should have exactly the four 'Commit A/B/C/D' described commits before the user starts."""
    r = _jj(
        "log", "-r", 'description(substring:"Commit ")',
        "--no-graph", "-T", 'description.first_line() ++ "\n"',
    )
    assert r.returncode == 0, f"'jj log' failed: {r.stderr}"
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert sorted(lines) == ["Commit A", "Commit B", "Commit C", "Commit D"], \
        f"Expected exactly four described commits, got: {lines!r}"


def test_working_copy_is_empty():
    """@ should start as an empty change (no file changes on top of D)."""
    r = _jj("log", "-r", "@", "--no-graph", "-T", "empty")
    assert r.returncode == 0, f"'jj log -r @ -T empty' failed: {r.stderr}"
    assert r.stdout.strip() == "true", \
        f"Expected @ to be empty initially, got: {r.stdout!r}"


def test_working_copy_parent_is_commit_d():
    """@- should be 'Commit D'."""
    r = _jj("log", "-r", "@-", "--no-graph", "-T", "description.first_line()")
    assert r.returncode == 0, f"'jj log -r @-' failed: {r.stderr}"
    assert "Commit D" in r.stdout, \
        f"Expected @- description to be 'Commit D', got: {r.stdout!r}"


def test_b_extra_file_does_not_exist_initially():
    """b_extra.txt must NOT exist anywhere in the initial repo state."""
    p = os.path.join(PROJECT_DIR, "b_extra.txt")
    assert not os.path.exists(p), \
        f"{p} must not exist in the initial state."


def test_initial_workdir_contains_all_four_files():
    """Working copy tip starts on top of D, so a.txt..d.txt are all materialized."""
    for fname in ("a.txt", "b.txt", "c.txt", "d.txt"):
        p = os.path.join(PROJECT_DIR, fname)
        assert os.path.isfile(p), \
            f"Expected initial working copy to contain {p}."
