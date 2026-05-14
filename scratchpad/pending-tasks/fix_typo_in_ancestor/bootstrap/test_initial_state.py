import os
import shutil
import subprocess

import pytest

REPO_DIR = "/home/user/myrepo"


def _jj(args, **kwargs):
    return subprocess.run(
        ["jj", *args],
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        **kwargs,
    )


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_repo_dir_exists():
    assert os.path.isdir(REPO_DIR), f"Repository directory {REPO_DIR} does not exist."


def test_repo_is_colocated_jj_git_repo():
    assert os.path.isdir(os.path.join(REPO_DIR, ".jj")), (
        f"Expected colocated jj repository: {REPO_DIR}/.jj is missing."
    )
    assert os.path.isdir(os.path.join(REPO_DIR, ".git")), (
        f"Expected colocated jj repository: {REPO_DIR}/.git is missing."
    )


def test_user_identity_configured():
    name = _jj(["config", "get", "user.name"])
    email = _jj(["config", "get", "user.email"])
    assert name.returncode == 0 and name.stdout.strip(), (
        f"Expected user.name to be configured; got stdout={name.stdout!r} stderr={name.stderr!r}"
    )
    assert email.returncode == 0 and email.stdout.strip(), (
        f"Expected user.email to be configured; got stdout={email.stdout!r} stderr={email.stderr!r}"
    )


def test_chain_of_four_descriptions_present():
    result = _jj([
        "log",
        "-r",
        'description(substring:"Add greeting")::@',
        "--no-graph",
        "-T",
        'description.first_line() ++ "\\n"',
    ])
    assert result.returncode == 0, (
        f"`jj log` failed with stderr: {result.stderr}"
    )
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    # @ is an empty commit on top (its description may be empty), so we filter to the named ones.
    named = [ln for ln in lines if ln in {
        "Add greeting",
        "Add feature 1",
        "Add feature 2",
        "Add feature 3",
    }]
    # jj log default order is newest first.
    assert named == [
        "Add feature 3",
        "Add feature 2",
        "Add feature 1",
        "Add greeting",
    ], (
        f"Expected the four named commits as linear ancestors of @ in order "
        f"(newest first): ['Add feature 3', 'Add feature 2', 'Add feature 1', 'Add greeting']; "
        f"got: {named} (full output: {result.stdout!r})"
    )


def test_greeting_commit_has_typo_initially():
    result = _jj([
        "file",
        "show",
        "-r",
        'description(substring:"Add greeting")',
        "greeting.txt",
    ])
    assert result.returncode == 0, (
        f"`jj file show` failed for greeting.txt at the 'Add greeting' commit: {result.stderr}"
    )
    assert result.stdout == "Helo World\n", (
        f"Expected initial greeting.txt at 'Add greeting' to be 'Helo World\\n' "
        f"(with the typo), got {result.stdout!r}"
    )


def test_working_copy_tip_is_empty():
    # The current working copy commit should be empty (no diff).
    result = _jj(["diff", "-r", "@", "--summary"])
    assert result.returncode == 0, f"`jj diff` failed: {result.stderr}"
    assert result.stdout.strip() == "", (
        f"Expected @ to be an empty commit on top of 'Add feature 3'; "
        f"got non-empty diff:\n{result.stdout}"
    )


def test_feature_files_exist_in_working_copy():
    files = _jj(["file", "list", "-r", "@"])
    assert files.returncode == 0, f"`jj file list` failed: {files.stderr}"
    listing = files.stdout.splitlines()
    for expected in ["greeting.txt", "feature1.txt", "feature2.txt", "feature3.txt"]:
        assert expected in listing, (
            f"Expected {expected} to exist in working-copy tip; got listing: {listing}"
        )
