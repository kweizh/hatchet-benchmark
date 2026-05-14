import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"
OUTPUT_FILE = "/home/user/myrepo/alice_fixes.txt"


def _run_jj(*args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def _query_change_ids(revset):
    result = _run_jj("log", "-r", revset, "--no-graph", "-T", 'change_id ++ "\\n"')
    assert result.returncode == 0, (
        f"`jj log -r {revset!r}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_file_change_ids():
    with open(OUTPUT_FILE, "r") as f:
        content = f.read()
    return [line.strip() for line in content.splitlines() if line.strip()]


def test_output_file_exists():
    assert os.path.isfile(OUTPUT_FILE), (
        f"Expected output file {OUTPUT_FILE} to exist as a regular file."
    )


def test_output_file_matches_revset_query():
    file_ids = _read_file_change_ids()
    query_ids = _query_change_ids(
        'author(substring:"Alice") & description(substring:"fix")'
    )
    assert set(file_ids) == set(query_ids), (
        "Contents of alice_fixes.txt do not match the revset "
        "'author(substring:\"Alice\") & description(substring:\"fix\")'.\n"
        f"  file change IDs:  {sorted(set(file_ids))}\n"
        f"  query change IDs: {sorted(set(query_ids))}"
    )


def test_output_file_has_exactly_two_change_ids():
    file_ids = _read_file_change_ids()
    assert len(file_ids) == 2, (
        f"Expected exactly 2 change IDs in {OUTPUT_FILE}, got {len(file_ids)}: {file_ids}"
    )
    assert len(set(file_ids)) == 2, (
        f"Expected the 2 change IDs in {OUTPUT_FILE} to be distinct, got duplicates: {file_ids}"
    )


def test_repo_history_unchanged_alice_count():
    ids = _query_change_ids('author(substring:"Alice")')
    assert len(ids) == 3, (
        f"Expected Alice to still have 3 commits after the task, got {len(ids)}: {ids}"
    )


def test_repo_history_unchanged_bob_count():
    ids = _query_change_ids('author(substring:"Bob")')
    assert len(ids) == 1, (
        f"Expected Bob to still have 1 commit after the task, got {len(ids)}: {ids}"
    )


def test_repo_history_unchanged_charlie_count():
    ids = _query_change_ids('author(substring:"Charlie")')
    assert len(ids) == 1, (
        f"Expected Charlie to still have 1 commit after the task, got {len(ids)}: {ids}"
    )
