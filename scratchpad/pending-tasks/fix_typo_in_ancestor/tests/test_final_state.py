import os
import shutil
import subprocess

import pytest

REPO_DIR = "/home/user/myrepo"

NAMED_DESCRIPTIONS = [
    "Add greeting",
    "Add feature 1",
    "Add feature 2",
    "Add feature 3",
]


def _jj(args, **kwargs):
    return subprocess.run(
        ["jj", *args],
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        **kwargs,
    )


def test_jj_binary_still_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_chain_is_preserved_as_ancestors_of_at():
    """The four named commits must still form a linear chain of ancestors of @,
    in the documented order."""
    result = _jj([
        "log",
        "-r",
        'description(substring:"Add greeting")::@',
        "--no-graph",
        "-T",
        'description.first_line() ++ "\\n"',
    ])
    assert result.returncode == 0, f"`jj log` failed: {result.stderr}"
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    named = [ln for ln in lines if ln in set(NAMED_DESCRIPTIONS)]
    # jj log lists newest first.
    expected = list(reversed(NAMED_DESCRIPTIONS))
    assert named == expected, (
        f"Expected the four named commits to remain as a linear ancestor chain of @ "
        f"(newest first): {expected}; got: {named}. "
        f"Full log output: {result.stdout!r}"
    )


def test_typo_fixed_at_oldest_commit():
    """Priority 1 (CLI): use `jj file show` at the 'Add greeting' commit."""
    result = _jj([
        "file",
        "show",
        "-r",
        'description(substring:"Add greeting")',
        "greeting.txt",
    ])
    assert result.returncode == 0, (
        f"`jj file show` failed at the 'Add greeting' commit: {result.stderr}"
    )
    assert result.stdout == "Hello World\n", (
        f"Expected greeting.txt at the 'Add greeting' commit to be 'Hello World\\n' "
        f"(no typo); got: {result.stdout!r}"
    )


def test_typo_fixed_at_working_copy_tip():
    """The fix must propagate to @ via automatic descendant rebase."""
    result = _jj(["file", "show", "-r", "@", "greeting.txt"])
    assert result.returncode == 0, (
        f"`jj file show -r @ greeting.txt` failed: {result.stderr}"
    )
    assert result.stdout == "Hello World\n", (
        f"Expected greeting.txt at the working-copy tip @ to be 'Hello World\\n'; "
        f"got: {result.stdout!r}"
    )


def test_no_named_commit_still_has_typo():
    """At every commit in the named chain, greeting.txt must NOT contain 'Helo World'."""
    for desc in NAMED_DESCRIPTIONS:
        result = _jj([
            "file",
            "show",
            "-r",
            f'description(substring:"{desc}")',
            "greeting.txt",
        ])
        assert result.returncode == 0, (
            f"`jj file show` failed at commit with description {desc!r}: {result.stderr}"
        )
        assert "Helo World" not in result.stdout, (
            f"Expected the typo 'Helo World' to be absent from greeting.txt at commit "
            f"{desc!r}, but found it. Content: {result.stdout!r}"
        )
        assert "Hello World" in result.stdout, (
            f"Expected greeting.txt at commit {desc!r} to contain the corrected "
            f"'Hello World'. Content: {result.stdout!r}"
        )


def test_feature_files_still_present_at_tip():
    files = _jj(["file", "list", "-r", "@"])
    assert files.returncode == 0, f"`jj file list` failed: {files.stderr}"
    listing = files.stdout.splitlines()
    for expected in ["greeting.txt", "feature1.txt", "feature2.txt", "feature3.txt"]:
        assert expected in listing, (
            f"Expected {expected} to still exist in the working-copy tip @; "
            f"got listing: {listing}"
        )


def test_chain_length_is_exactly_four_named_commits():
    """No commits with the named descriptions were duplicated or removed."""
    for desc in NAMED_DESCRIPTIONS:
        result = _jj([
            "log",
            "-r",
            f'description(substring:"{desc}")',
            "--no-graph",
            "-T",
            'change_id ++ "\\n"',
        ])
        assert result.returncode == 0, (
            f"`jj log` failed for description {desc!r}: {result.stderr}"
        )
        ids = [ln for ln in result.stdout.splitlines() if ln.strip()]
        assert len(ids) == 1, (
            f"Expected exactly 1 commit with description {desc!r}, found {len(ids)}: {ids}"
        )
