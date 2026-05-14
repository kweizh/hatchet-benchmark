import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/myrepo"


def test_parent_description_is_set():
    """The previous working-copy commit (@-) must have the description 'Add README documentation'."""
    result = subprocess.run(
        ["jj", "log", "-r", "@-", "--no-graph", "-T", "description"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj log -r @- -T description' failed: {result.stderr}"
    assert result.stdout.strip() == "Add README documentation", \
        f"Expected @- description to be 'Add README documentation', got: {result.stdout!r}"


def test_working_copy_is_new_empty_change():
    """The current working-copy commit (@) must be a newly created empty change."""
    result = subprocess.run(
        ["jj", "log", "-r", "@", "--no-graph", "-T", "empty"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj log -r @ -T empty' failed: {result.stderr}"
    assert result.stdout.strip() == "true", \
        f"Expected new working copy @ to be empty (empty=true), got: {result.stdout!r}"


def test_working_copy_description_is_empty():
    """The new working-copy commit (@) should have no description yet."""
    result = subprocess.run(
        ["jj", "log", "-r", "@", "--no-graph", "-T", "description"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj log -r @ -T description' failed: {result.stderr}"
    assert result.stdout.strip() == "", \
        f"Expected the new working copy @ to have an empty description, got: {result.stdout!r}"


def test_parent_contains_readme_change():
    """The previous commit (@-) must contain the README.md change."""
    result = subprocess.run(
        ["jj", "diff", "-r", "@-", "--summary"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj diff -r @- --summary' failed: {result.stderr}"
    assert "README.md" in result.stdout, \
        f"Expected README.md to be modified in @-, got: {result.stdout!r}"


def test_parent_first_line_description():
    """The first line of the @- description must match the expected message."""
    result = subprocess.run(
        ["jj", "log", "-r", "@-", "--no-graph", "-T", "description.first_line()"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    assert result.returncode == 0, \
        f"'jj log -r @- -T description.first_line()' failed: {result.stderr}"
    assert result.stdout.strip() == "Add README documentation", \
        f"Expected first line of @- description to be 'Add README documentation', got: {result.stdout!r}"
