import os
import subprocess

PROJECT_DIR = "/home/user/myrepo"
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.yaml")
EXPECTED_CONTENT = "timeout: 90\n"


def _run_jj(*args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_config_yaml_exact_content():
    with open(CONFIG_FILE, "rb") as f:
        content = f.read()
    expected_bytes = EXPECTED_CONTENT.encode("utf-8")
    assert content == expected_bytes, (
        f"Expected {CONFIG_FILE} content to be exactly {expected_bytes!r}, got {content!r}"
    )


def test_no_conflicted_commits_remain():
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
    assert len(lines) == 0, (
        f"Expected `jj log -r 'conflicts()'` to be empty after resolution, got {lines!r}"
    )


def test_jj_status_reports_no_conflict():
    result = _run_jj("status")
    assert result.returncode == 0, (
        f"`jj status` failed in {PROJECT_DIR}: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    combined = (result.stdout + result.stderr).lower()
    assert "conflict" not in combined, (
        f"Expected `jj status` to NOT mention any conflict after resolution, got stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_branch_a_still_points_to_increase_60():
    result = _run_jj("log", "-r", "branch-a", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r branch-a` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Increase timeout to 60", (
        f"Expected `branch-a` to still point to commit with description 'Increase timeout to 60', got {result.stdout!r}"
    )


def test_branch_b_still_points_to_increase_120():
    result = _run_jj("log", "-r", "branch-b", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r branch-b` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Increase timeout to 120", (
        f"Expected `branch-b` to still point to commit with description 'Increase timeout to 120', got {result.stdout!r}"
    )


def test_branch_b_parent_is_branch_a():
    result = _run_jj("log", "-r", "branch-b-", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r branch-b-` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Increase timeout to 60", (
        f"Expected the parent of `branch-b` (branch-b-) to be the `Increase timeout to 60` commit (branch-a), got {result.stdout!r}"
    )


def test_base_bookmark_unchanged():
    result = _run_jj("log", "-r", "base", "--no-graph", "-T", "description.first_line()")
    assert result.returncode == 0, (
        f"`jj log -r base` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Base", (
        f"Expected `base` bookmark to still point to commit with description 'Base', got {result.stdout!r}"
    )


def test_resolution_recorded_in_branch_b_commit():
    # `jj file show -r branch-b config.yaml` reads from the commit (not the
    # working copy), proving that the resolution was auto-snapshotted onto
    # the branch-b commit and the conflict was cleared from the commit.
    result = _run_jj("file", "show", "-r", "branch-b", "config.yaml")
    assert result.returncode == 0, (
        f"`jj file show -r branch-b config.yaml` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout == EXPECTED_CONTENT, (
        f"Expected branch-b commit to contain config.yaml = {EXPECTED_CONTENT!r}, got {result.stdout!r}"
    )
