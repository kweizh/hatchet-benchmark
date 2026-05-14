import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def _get_feature_a_change_ids():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Feature A")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for description(substring:\"Feature A\") failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def test_at_least_two_feature_a_commits():
    change_ids = _get_feature_a_change_ids()
    assert len(change_ids) >= 2, (
        f"Expected at least 2 commits with description 'Feature A' after `jj duplicate`, found {len(change_ids)}: {change_ids}"
    )


def test_feature_a_change_ids_are_distinct():
    change_ids = _get_feature_a_change_ids()
    assert len(change_ids) >= 2, (
        f"Expected at least 2 distinct change IDs with description 'Feature A', got {change_ids}"
    )
    assert len(set(change_ids)) == len(change_ids), (
        f"Expected all change IDs for 'Feature A' to be distinct, got duplicates in: {change_ids}"
    )


def test_each_feature_a_commit_contains_correct_file():
    change_ids = _get_feature_a_change_ids()
    assert len(change_ids) >= 2, (
        f"Expected at least 2 commits with description 'Feature A', got {change_ids}"
    )
    for cid in change_ids:
        result = subprocess.run(
            ["jj", "file", "show", "-r", cid, "feature_a.txt"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"`jj file show -r {cid} feature_a.txt` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert result.stdout.strip() == "feature A content", (
            f"Expected feature_a.txt in commit {cid} to contain 'feature A content', got {result.stdout!r}"
        )
