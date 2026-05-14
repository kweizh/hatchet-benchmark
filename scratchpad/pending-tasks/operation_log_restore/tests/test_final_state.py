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


def test_stage1_present():
    ids = _get_change_ids_for_description("Stage 1")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Stage 1' after restore, "
        f"got {len(ids)}: {ids}"
    )


def test_stage2_restored():
    ids = _get_change_ids_for_description("Stage 2")
    assert len(ids) == 1, (
        f"Expected exactly one commit with description 'Stage 2' to be restored via "
        f"`jj op restore`, got {len(ids)}: {ids}"
    )
    assert ids[0] != "", "Expected a non-empty change ID for the restored 'Stage 2'."


def test_stage3_absent():
    ids = _get_change_ids_for_description("Stage 3")
    assert len(ids) == 0, (
        f"Expected NO commit with description 'Stage 3' in the restored state, "
        f"got {len(ids)}: {ids}"
    )


def test_extra1_absent():
    ids = _get_change_ids_for_description("extra1")
    assert len(ids) == 0, (
        f"Expected NO commit with description 'extra1' in the restored state, "
        f"got {len(ids)}: {ids}"
    )


def test_extra2_absent():
    ids = _get_change_ids_for_description("extra2")
    assert len(ids) == 0, (
        f"Expected NO commit with description 'extra2' in the restored state, "
        f"got {len(ids)}: {ids}"
    )


def test_stage2_parent_is_stage1():
    """Verify the linear chain Stage 1 -> Stage 2 is restored."""
    result = subprocess.run(
        [
            "jj",
            "log",
            "-r",
            'description(substring:"Stage 2")-',
            "--no-graph",
            "-T",
            'description ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj log -r 'description(substring:\"Stage 2\")-'` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "Stage 1" in result.stdout, (
        f"Expected parent of 'Stage 2' to be 'Stage 1' (linear chain restored), "
        f"got: {result.stdout!r}"
    )


def test_file1_exists_on_disk():
    file1 = os.path.join(PROJECT_DIR, "file1.txt")
    assert os.path.isfile(file1), (
        f"Expected {file1} to exist on disk after restore."
    )
    with open(file1) as f:
        content = f.read().strip()
    assert content == "content A", (
        f"Expected file1.txt content to be 'content A', got {content!r}"
    )


def test_file2_exists_on_disk_with_content():
    file2 = os.path.join(PROJECT_DIR, "file2.txt")
    assert os.path.isfile(file2), (
        f"Expected {file2} to exist on disk after restore (recovered via `jj op restore`)."
    )
    with open(file2) as f:
        content = f.read().strip()
    assert content == "content B", (
        f"Expected file2.txt content to be 'content B', got {content!r}"
    )


def test_file3_absent_on_disk():
    file3 = os.path.join(PROJECT_DIR, "file3.txt")
    assert not os.path.exists(file3), (
        f"Expected {file3} to NOT exist on disk after restore (Stage 3 was removed by "
        f"the restore), but the file is still present."
    )


def test_most_recent_operation_is_restore():
    """Confirm `jj op restore` was the most recent operation in the op log."""
    result = subprocess.run(
        [
            "jj",
            "op",
            "log",
            "--no-graph",
            "-T",
            'self.description() ++ "\\n"',
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj op log` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) > 0, f"`jj op log` produced no operation entries: {result.stdout!r}"
    most_recent = lines[0].lower()
    assert "restore" in most_recent, (
        f"Expected the most recent operation in `jj op log` to be a 'restore' operation, "
        f"confirming the agent used `jj op restore`. Most recent: {lines[0]!r}; "
        f"full op log descriptions: {lines!r}"
    )


def test_stage2_change_contains_file2():
    """Verify that the restored Stage 2 commit actually contains file2.txt with the
    expected content (not merely an empty commit with the description 'Stage 2')."""
    result = subprocess.run(
        [
            "jj",
            "file",
            "show",
            "-r",
            'description(substring:"Stage 2")',
            "file2.txt",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`jj file show -r 'description(substring:\"Stage 2\")' file2.txt` failed: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "content B", (
        f"Expected file2.txt at the restored Stage 2 commit to contain 'content B', "
        f"got: {result.stdout!r}"
    )
