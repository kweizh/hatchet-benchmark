import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def _commit_lines_for(description):
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            f'description(substring:"{description}")',
            "--no-graph",
            "-T",
            'description.first_line() ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for description {description!r} failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_feature_bookmark_still_exists():
    """Priority 1: Verify with jj CLI that the bookmark 'feature' still exists locally."""
    result = subprocess.run(
        ["jj", "bookmark", "list", "feature"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj bookmark list feature` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "feature" in result.stdout and result.stdout.strip() != "", (
        f"Expected local bookmark 'feature' to still exist after the move, got: {result.stdout!r}"
    )


def test_feature_bookmark_points_to_commit_3():
    """Priority 1: Verify with jj CLI that the bookmark resolves to the commit with description 'Commit 3'."""
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            "feature",
            "--no-graph",
            "-T",
            "description.first_line()",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r feature` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Commit 3", (
        f"Expected the 'feature' bookmark to point to the commit with description 'Commit 3', got: {result.stdout!r}"
    )


def test_commit_1_still_exists_unmodified():
    lines = _commit_lines_for("Commit 1")
    assert len(lines) == 1, (
        f"Expected exactly one commit with description 'Commit 1' after the move, got {len(lines)}: {lines}"
    )
    assert lines[0] == "Commit 1", (
        f"Expected the description to still be exactly 'Commit 1', got: {lines[0]!r}"
    )


def test_commit_2_still_exists_unmodified():
    lines = _commit_lines_for("Commit 2")
    assert len(lines) == 1, (
        f"Expected exactly one commit with description 'Commit 2' after the move, got {len(lines)}: {lines}"
    )
    assert lines[0] == "Commit 2", (
        f"Expected the description to still be exactly 'Commit 2', got: {lines[0]!r}"
    )


def test_commit_3_still_exists_unmodified():
    lines = _commit_lines_for("Commit 3")
    assert len(lines) == 1, (
        f"Expected exactly one commit with description 'Commit 3' after the move, got {len(lines)}: {lines}"
    )
    assert lines[0] == "Commit 3", (
        f"Expected the description to still be exactly 'Commit 3', got: {lines[0]!r}"
    )
