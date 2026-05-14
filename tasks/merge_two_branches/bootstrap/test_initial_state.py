import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"


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


def test_jj_status_runs():
    result = subprocess.run(
        ["jj", "status"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR}: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_user_identity_configured():
    result_name = subprocess.run(
        ["jj", "config", "get", "user.name"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_name.returncode == 0 and result_name.stdout.strip() != "", (
        f"Expected user.name to be configured, got rc={result_name.returncode} stdout={result_name.stdout!r} stderr={result_name.stderr!r}"
    )
    result_email = subprocess.run(
        ["jj", "config", "get", "user.email"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result_email.returncode == 0 and result_email.stdout.strip() != "", (
        f"Expected user.email to be configured, got rc={result_email.returncode} stdout={result_email.stdout!r} stderr={result_email.stderr!r}"
    )


def test_branch_x_bookmark_points_to_branch_x_commit():
    result = subprocess.run(
        ["jj", "log", "-r", "branch_x", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r branch_x` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Branch X commit", (
        f"Expected `branch_x` bookmark to point to a commit with description 'Branch X commit', got {result.stdout!r}"
    )


def test_branch_y_bookmark_points_to_branch_y_commit():
    result = subprocess.run(
        ["jj", "log", "-r", "branch_y", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r branch_y` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Branch Y commit", (
        f"Expected `branch_y` bookmark to point to a commit with description 'Branch Y commit', got {result.stdout!r}"
    )


def test_base_commit_exists_and_is_common_ancestor():
    # Exactly one Base commit.
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Base commit")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for Base commit failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, (
        f"Expected exactly one commit with description 'Base commit', got {len(lines)}: {lines}"
    )


def test_branch_x_parent_is_base():
    result = subprocess.run(
        ["jj", "log", "-r", "branch_x-", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r branch_x-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Base commit", (
        f"Expected parent of `branch_x` to have description 'Base commit', got {result.stdout!r}"
    )


def test_branch_y_parent_is_base():
    result = subprocess.run(
        ["jj", "log", "-r", "branch_y-", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r branch_y-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Base commit", (
        f"Expected parent of `branch_y` to have description 'Base commit', got {result.stdout!r}"
    )


def test_no_merge_commit_initially():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Merge branches")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for Merge branches failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 0, (
        f"Expected no commit with description containing 'Merge branches' in the initial state, got {len(lines)}: {lines}"
    )


def test_branch_x_tip_has_shared_and_x_files():
    for name, expected in [("shared.txt", "shared content"), ("x.txt", "x")]:
        result = subprocess.run(
            ["jj", "file", "show", "-r", "branch_x", name],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"`jj file show -r branch_x {name}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert result.stdout.strip() == expected, (
            f"Expected {name} at branch_x tip to contain {expected!r}, got {result.stdout!r}"
        )


def test_branch_y_tip_has_shared_and_y_files():
    for name, expected in [("shared.txt", "shared content"), ("y.txt", "y")]:
        result = subprocess.run(
            ["jj", "file", "show", "-r", "branch_y", name],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"`jj file show -r branch_y {name}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert result.stdout.strip() == expected, (
            f"Expected {name} at branch_y tip to contain {expected!r}, got {result.stdout!r}"
        )


def test_branch_x_tip_does_not_have_y_file():
    # branch_x and branch_y modify disjoint files; y.txt must not exist at branch_x tip.
    result = subprocess.run(
        ["jj", "file", "show", "-r", "branch_x", "y.txt"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"Did not expect y.txt to be present at branch_x tip, got stdout={result.stdout!r}"
    )


def test_branch_y_tip_does_not_have_x_file():
    result = subprocess.run(
        ["jj", "file", "show", "-r", "branch_y", "x.txt"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"Did not expect x.txt to be present at branch_y tip, got stdout={result.stdout!r}"
    )
