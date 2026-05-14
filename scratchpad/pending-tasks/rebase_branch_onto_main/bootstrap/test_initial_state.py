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


def test_main_bookmark_points_to_main2():
    result = subprocess.run(
        ["jj", "log", "-r", "main", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r main` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Main2", (
        f"Expected `main` bookmark to point to commit with description 'Main2', got {result.stdout!r}"
    )


def test_feature_bookmark_points_to_feat2_initially():
    result = subprocess.run(
        ["jj", "log", "-r", "feature", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r feature` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Feat2", (
        f"Expected `feature` bookmark to point to commit with description 'Feat2' initially, got {result.stdout!r}"
    )


def test_feature_initially_does_not_descend_from_main():
    # Initially, feature and main share only the Base ancestor, so the
    # parent of feature (Feat1) must NOT have description 'Main2'.
    result = subprocess.run(
        ["jj", "log", "-r", "feature-", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r feature-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Feat1", (
        f"Expected the parent of `feature` to have description 'Feat1' initially, got {result.stdout!r}"
    )


def test_initial_base_commit_exists():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Base")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for Base failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, (
        f"Expected exactly one commit with description 'Base', got {len(lines)}: {lines}"
    )


def test_main_branch_has_two_commits():
    # The 'main' branch (relative to Base): commits in main not in Base
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Base")..main',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for main..feature failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2, (
        f"Expected exactly 2 commits between 'Base' and 'main' initially, got {len(lines)}: {lines}"
    )


def test_feature_branch_initially_has_two_commits_off_base():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Base")..feature',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for Base..feature failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2, (
        f"Expected exactly 2 commits between 'Base' and 'feature' initially, got {len(lines)}: {lines}"
    )


def test_main_tip_has_main_files():
    for name, expected in [("main1.txt", "main1 content"), ("main2.txt", "main2 content")]:
        result = subprocess.run(
            ["jj", "file", "show", "-r", "main", name],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"`jj file show -r main {name}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert result.stdout.strip() == expected, (
            f"Expected {name} at main tip to contain {expected!r}, got {result.stdout!r}"
        )


def test_feature_tip_has_feat_files():
    for name, expected in [("feat1.txt", "feat1 content"), ("feat2.txt", "feat2 content")]:
        result = subprocess.run(
            ["jj", "file", "show", "-r", "feature", name],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"`jj file show -r feature {name}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert result.stdout.strip() == expected, (
            f"Expected {name} at feature tip to contain {expected!r}, got {result.stdout!r}"
        )
