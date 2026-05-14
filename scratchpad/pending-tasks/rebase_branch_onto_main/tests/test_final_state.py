import os
import subprocess

PROJECT_DIR = "/home/user/myrepo"


def _jj_log_first_line(revset: str) -> str:
    result = subprocess.run(
        ["jj", "log", "-r", revset, "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r {revset!r}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return result.stdout.strip()


def _jj_file_show(revset: str, path: str) -> str:
    result = subprocess.run(
        ["jj", "file", "show", "-r", revset, path],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show -r {revset!r} {path}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return result.stdout


def test_feature_tip_is_feat2():
    desc = _jj_log_first_line("feature")
    assert desc == "Feat2", (
        f"Expected `feature` bookmark to point to commit with description 'Feat2', got {desc!r}"
    )


def test_feature_parent_is_feat1():
    desc = _jj_log_first_line("feature-")
    assert desc == "Feat1", (
        f"Expected parent of `feature` (feature-) to have description 'Feat1', got {desc!r}"
    )


def test_feature_grandparent_is_main2():
    desc = _jj_log_first_line("feature--")
    assert desc == "Main2", (
        f"Expected grandparent of `feature` (feature--) to have description 'Main2' after rebase onto main, got {desc!r}"
    )


def test_main_bookmark_unchanged():
    desc = _jj_log_first_line("main")
    assert desc == "Main2", (
        f"Expected `main` bookmark to still point to commit with description 'Main2' (unchanged), got {desc!r}"
    )


def test_exactly_two_commits_between_main_and_feature():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            "main..feature",
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r main..feature` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2, (
        f"Expected exactly 2 commits in `main..feature` after rebase, got {len(lines)}: {lines}"
    )
    # Ensure the two change IDs are distinct (sanity check).
    assert len(set(lines)) == 2, (
        f"Expected two distinct change IDs in `main..feature`, got duplicates: {lines}"
    )


def test_feature_tip_contains_feat2_file():
    content = _jj_file_show("feature", "feat2.txt")
    assert content.strip() == "feat2 content", (
        f"Expected feat2.txt at feature tip to contain 'feat2 content', got {content!r}"
    )


def test_feature_tip_contains_feat1_file():
    content = _jj_file_show("feature", "feat1.txt")
    assert content.strip() == "feat1 content", (
        f"Expected feat1.txt at feature tip to contain 'feat1 content', got {content!r}"
    )


def test_feature_tip_contains_main2_file():
    # After rebase, the feature tip's history includes Main2, so main2.txt
    # must be visible at the feature tip.
    content = _jj_file_show("feature", "main2.txt")
    assert content.strip() == "main2 content", (
        f"Expected main2.txt at feature tip to contain 'main2 content', got {content!r}"
    )


def test_feature_tip_contains_main1_file():
    content = _jj_file_show("feature", "main1.txt")
    assert content.strip() == "main1 content", (
        f"Expected main1.txt at feature tip to contain 'main1 content', got {content!r}"
    )


def test_feature_tip_contains_base_file():
    content = _jj_file_show("feature", "base.txt")
    assert content.strip() == "base content", (
        f"Expected base.txt at feature tip to contain 'base content', got {content!r}"
    )
