import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def _get_change_ids_for_description(substring):
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            f'description(substring:"{substring}")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log` for description '{substring}' failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def test_commit_b_restored_with_single_change_id():
    ids = _get_change_ids_for_description("Commit B")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit B' after abandon+undo, "
        f"got {len(ids)}: {ids}"
    )
    assert ids[0] != "", "Expected a non-empty change ID for the restored 'Commit B'."


def test_commit_a_still_exists():
    ids = _get_change_ids_for_description("Commit A")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit A', got {len(ids)}: {ids}"
    )


def test_commit_c_still_exists():
    ids = _get_change_ids_for_description("Commit C")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Commit C', got {len(ids)}: {ids}"
    )


def test_chain_b_parent_is_a():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Commit B")-',
            "--no-graph",
            "-T",
            'description ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Commit B\")-'` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "Commit A" in result.stdout, (
        f"Expected parent of 'Commit B' to be 'Commit A' (linear chain restored), "
        f"got: {result.stdout!r}"
    )


def test_chain_c_parent_is_b():
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Commit C")-',
            "--no-graph",
            "-T",
            'description ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Commit C\")-'` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "Commit B" in result.stdout, (
        f"Expected parent of 'Commit C' to be 'Commit B' (linear chain restored), "
        f"got: {result.stdout!r}"
    )


@pytest.mark.parametrize("filename,expected", [
    ("a.txt", "content A"),
    ("b.txt", "content B"),
    ("c.txt", "content C"),
])
def test_tip_contains_all_three_files(filename, expected):
    result = subprocess.run(
        ["jj", "file", "show", "-r", 'description(substring:"Commit C")', filename],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show -r 'description(substring:\"Commit C\")' {filename}` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == expected, (
        f"Expected {filename} content at the tip (Commit C) to be {expected!r}, "
        f"got {result.stdout!r}"
    )


def _get_op_log_descriptions():
    result = subprocess.run(
        ["jj", "op", "log", "--no-graph", "-T", 'description ++ "\\n"'],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj op log` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return result.stdout


def test_op_log_contains_abandon_operation():
    op_log = _get_op_log_descriptions().lower()
    assert "abandon" in op_log, (
        f"Expected `jj op log` to contain an 'abandon' operation entry, got: {op_log!r}"
    )


def test_op_log_contains_undo_operation():
    op_log = _get_op_log_descriptions().lower()
    assert "undo" in op_log, (
        f"Expected `jj op log` to contain an 'undo' operation entry, got: {op_log!r}"
    )
