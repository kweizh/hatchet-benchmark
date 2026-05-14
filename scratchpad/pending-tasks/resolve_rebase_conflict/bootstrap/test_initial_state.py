import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.yaml")


def _run_jj(*args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


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


def test_user_identity_configured():
    name_res = _run_jj("config", "get", "user.name")
    assert name_res.returncode == 0 and name_res.stdout.strip() != "", (
        f"Expected user.name to be configured, got rc={name_res.returncode} stdout={name_res.stdout!r} stderr={name_res.stderr!r}"
    )
    email_res = _run_jj("config", "get", "user.email")
    assert email_res.returncode == 0 and email_res.stdout.strip() != "", (
        f"Expected user.email to be configured, got rc={email_res.returncode} stdout={email_res.stdout!r} stderr={email_res.stderr!r}"
    )


def test_config_yaml_exists():
    assert os.path.isfile(CONFIG_FILE), (
        f"Expected {CONFIG_FILE} to exist in the working copy."
    )


def test_config_yaml_has_jj_conflict_markers():
    with open(CONFIG_FILE, "r") as f:
        content = f.read()
    assert "<<<<<<<" in content, (
        f"Expected config.yaml to contain a jj conflict start marker '<<<<<<<' in the working copy, got:\n{content!r}"
    )
    assert ">>>>>>>" in content, (
        f"Expected config.yaml to contain a jj conflict end marker '>>>>>>>' in the working copy, got:\n{content!r}"
    )


def test_jj_status_reports_a_conflict():
    result = _run_jj("status")
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR}: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    combined = (result.stdout + result.stderr).lower()
    assert "conflict" in combined, (
        f"Expected `jj status` to mention a conflict in the working copy, got stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_at_least_one_conflicted_commit_exists():
    result = _run_jj(
        "log",
        "-r",
        "conflicts()",
        "--no-graph",
        "-T",
        'change_id ++ "\\n"',
    )
    assert result.returncode == 0, (
        f"`jj log -r 'conflicts()'` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) >= 1, (
        f"Expected at least one commit with conflicts initially, got {len(lines)} lines: {lines!r}"
    )


def test_base_bookmark_points_to_base():
    result = _run_jj("log", "-r", "base", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r base` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Base", (
        f"Expected `base` bookmark to point to commit with description 'Base', got {result.stdout!r}"
    )


def test_branch_a_points_to_increase_60():
    result = _run_jj("log", "-r", "branch-a", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r branch-a` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Increase timeout to 60", (
        f"Expected `branch-a` bookmark to point to commit with description 'Increase timeout to 60', got {result.stdout!r}"
    )


def test_branch_b_points_to_increase_120():
    result = _run_jj("log", "-r", "branch-b", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r branch-b` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Increase timeout to 120", (
        f"Expected `branch-b` bookmark to point to commit with description 'Increase timeout to 120', got {result.stdout!r}"
    )


def test_branch_b_parent_is_branch_a():
    # After the initial rebase, branch-b should be a child of branch-a
    # (so branch-b- has description "Increase timeout to 60").
    result = _run_jj("log", "-r", "branch-b-", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r branch-b-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Increase timeout to 60", (
        f"Expected the parent of `branch-b` to be the `Increase timeout to 60` commit (branch-a) after the initial rebase, got {result.stdout!r}"
    )
