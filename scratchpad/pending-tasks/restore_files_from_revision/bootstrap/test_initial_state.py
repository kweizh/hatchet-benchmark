import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"


def _run_jj(args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_repo_is_colocated_jj_repo():
    assert os.path.isdir(os.path.join(PROJECT_DIR, ".jj")), (
        f"Expected a .jj directory at {PROJECT_DIR}/.jj (colocated jj repo)."
    )
    assert os.path.isdir(os.path.join(PROJECT_DIR, ".git")), (
        f"Expected a .git directory at {PROJECT_DIR}/.git (colocated jj repo)."
    )


def test_user_identity_configured():
    name = _run_jj(["config", "get", "user.name"])
    email = _run_jj(["config", "get", "user.email"])
    assert name.returncode == 0 and name.stdout.strip(), (
        f"user.name is not configured: stdout={name.stdout!r} stderr={name.stderr!r}"
    )
    assert email.returncode == 0 and email.stdout.strip(), (
        f"user.email is not configured: stdout={email.stdout!r} stderr={email.stderr!r}"
    )


def test_config_json_exists_with_v2_content():
    config_path = os.path.join(PROJECT_DIR, "config.json")
    assert os.path.isfile(config_path), f"Expected file {config_path} to exist."
    with open(config_path) as f:
        content = f.read()
    assert '{"version": "2.0"}' in content, (
        f"Expected config.json on disk to currently contain '{{\"version\": \"2.0\"}}', "
        f"got: {content!r}"
    )


def test_extra_txt_exists_with_initial_content():
    extra_path = os.path.join(PROJECT_DIR, "extra.txt")
    assert os.path.isfile(extra_path), f"Expected file {extra_path} to exist."
    with open(extra_path) as f:
        content = f.read()
    assert "additional data" in content, (
        f"Expected extra.txt to contain 'additional data', got: {content!r}"
    )


def test_working_copy_is_empty_initially():
    result = _run_jj(["log", "-r", "@", "--no-graph", "-T", "empty"])
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "true", (
        f"Expected working copy @ to be empty initially, got empty={result.stdout!r}"
    )


def test_working_copy_description_is_empty():
    result = _run_jj(["log", "-r", "@", "--no-graph", "-T", "description"])
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "", (
        f"Expected working-copy description to be empty, got: {result.stdout!r}"
    )


def test_parent_commit_description_is_update_config():
    result = _run_jj(["log", "-r", "@-", "--no-graph", "-T", "description.first_line()"])
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Update config and add extras", (
        f"Expected parent commit description to be 'Update config and add extras', "
        f"got: {result.stdout!r}"
    )


def test_grandparent_commit_description_is_initial_config():
    result = _run_jj(["log", "-r", "@--", "--no-graph", "-T", "description.first_line()"])
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Initial config", (
        f"Expected grandparent commit description to be 'Initial config', "
        f"got: {result.stdout!r}"
    )


def test_initial_config_commit_resolvable_via_description_substring():
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Initial config")',
            "--no-graph",
            "-T",
            "description.first_line()",
        ]
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Initial config", (
        f"Expected revset 'description(substring:\"Initial config\")' to resolve "
        f"to exactly the 'Initial config' commit, got: {result.stdout!r}"
    )


def test_parent_commit_diff_modifies_config_and_adds_extra():
    result = _run_jj(["diff", "-r", "@-", "--git"])
    assert result.returncode == 0, (
        f"jj diff failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    diff = result.stdout
    assert "config.json" in diff, (
        f"Expected `jj diff -r '@-' --git` to mention config.json, got: {diff!r}"
    )
    assert "extra.txt" in diff, (
        f"Expected `jj diff -r '@-' --git` to mention extra.txt, got: {diff!r}"
    )
    assert '+{"version": "2.0"}' in diff, (
        f"Expected `jj diff -r '@-' --git` to show the new content with version 2.0, "
        f"got: {diff!r}"
    )
    assert '-{"version": "1.0"}' in diff, (
        f"Expected `jj diff -r '@-' --git` to show the old content with version 1.0 "
        f"being removed, got: {diff!r}"
    )


def test_exactly_three_non_root_commits_initially():
    result = _run_jj(
        ["log", "-r", "~root()", "--no-graph", "-T", 'change_id ++ "\\n"']
    )
    assert result.returncode == 0, (
        f"jj log failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    change_ids = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(change_ids) == 3, (
        f"Expected exactly 3 non-root commits initially "
        f"(Initial config + Update config + empty @), got {len(change_ids)}: {change_ids}"
    )
