import os
import subprocess

PROJECT_DIR = "/home/user/myrepo"
CONFIG_JSON = os.path.join(PROJECT_DIR, "config.json")
EXTRA_TXT = os.path.join(PROJECT_DIR, "extra.txt")


def _run_jj(args):
    return subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_config_json_restored_to_v1():
    """Priority 3: config.json on disk must be the v1.0 content."""
    assert os.path.isfile(CONFIG_JSON), f"Expected {CONFIG_JSON} to exist."
    with open(CONFIG_JSON) as f:
        content = f.read()
    assert '{"version": "1.0"}' in content, (
        f"Expected config.json to contain '{{\"version\": \"1.0\"}}' after restore, "
        f"got: {content!r}"
    )
    assert '"2.0"' not in content, (
        f"Expected config.json to no longer contain version '2.0' after restore, "
        f"got: {content!r}"
    )


def test_extra_txt_still_present_with_original_content():
    """Priority 3: extra.txt must still be there untouched."""
    assert os.path.isfile(EXTRA_TXT), (
        f"Expected {EXTRA_TXT} to still exist after restoring config.json only."
    )
    with open(EXTRA_TXT) as f:
        content = f.read()
    assert "additional data" in content, (
        f"Expected extra.txt to still contain 'additional data', got: {content!r}"
    )


def test_initial_config_commit_still_exists():
    """Priority 1: The 'Initial config' commit must still exist with its description."""
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
        f"`jj log` for 'Initial config' failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Initial config", (
        f"Expected revset 'description(substring:\"Initial config\")' to resolve "
        f"to exactly 'Initial config', got: {result.stdout!r}"
    )


def test_update_config_commit_still_exists():
    """Priority 1: The 'Update config and add extras' commit must still exist."""
    result = _run_jj(
        [
            "log",
            "-r",
            'description(substring:"Update config and add extras")',
            "--no-graph",
            "-T",
            "description.first_line()",
        ]
    )
    assert result.returncode == 0, (
        f"`jj log` for 'Update config and add extras' failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "Update config and add extras", (
        f"Expected revset to resolve to 'Update config and add extras', "
        f"got: {result.stdout!r}"
    )


def test_update_config_commit_unchanged():
    """Priority 1: `jj diff -r 'description(substring:\"Update config...\")' --git`
    must still show config.json being set to 2.0 and extra.txt being added.
    """
    result = _run_jj(
        [
            "diff",
            "-r",
            'description(substring:"Update config and add extras")',
            "--git",
        ]
    )
    assert result.returncode == 0, (
        f"`jj diff` for 'Update config and add extras' failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    diff = result.stdout
    assert "config.json" in diff, (
        f"Expected diff of 'Update config and add extras' to mention config.json, "
        f"got: {diff!r}"
    )
    assert "extra.txt" in diff, (
        f"Expected diff of 'Update config and add extras' to mention extra.txt, "
        f"got: {diff!r}"
    )
    assert '+{"version": "2.0"}' in diff, (
        f"Expected diff of 'Update config and add extras' to still show "
        f"version 2.0 being introduced (+'{{\"version\": \"2.0\"}}'), got: {diff!r}"
    )
    assert '-{"version": "1.0"}' in diff, (
        f"Expected diff of 'Update config and add extras' to still show "
        f"version 1.0 being removed (-'{{\"version\": \"1.0\"}}'), got: {diff!r}"
    )
    assert "+additional data" in diff, (
        f"Expected diff of 'Update config and add extras' to still show "
        f"'additional data' being added in extra.txt, got: {diff!r}"
    )


def test_working_copy_diff_reverts_config_json():
    """Priority 1: `jj diff -r '@' --git` must show config.json being reverted in @."""
    result = _run_jj(["diff", "-r", "@", "--git"])
    assert result.returncode == 0, (
        f"`jj diff -r '@' --git` failed: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    diff = result.stdout
    assert "config.json" in diff, (
        f"Expected `jj diff -r '@' --git` to mention config.json, got: {diff!r}"
    )
    assert '+{"version": "1.0"}' in diff, (
        f"Expected `jj diff -r '@' --git` to show '+{{\"version\": \"1.0\"}}' "
        f"(the restored content), got: {diff!r}"
    )
    assert '-{"version": "2.0"}' in diff, (
        f"Expected `jj diff -r '@' --git` to show '-{{\"version\": \"2.0\"}}' "
        f"(the parent content being replaced — a revert), got: {diff!r}"
    )
    # extra.txt should NOT be affected by the working-copy change
    assert "extra.txt" not in diff, (
        f"Expected `jj diff -r '@' --git` to NOT touch extra.txt (only config.json "
        f"should be restored), got: {diff!r}"
    )


def test_working_copy_is_not_empty_after_restore():
    """Priority 1: After `jj restore`, the working copy @ is no longer empty."""
    result = _run_jj(["log", "-r", "@", "--no-graph", "-T", "empty"])
    assert result.returncode == 0, (
        f"`jj log -r '@'` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "false", (
        f"Expected working copy @ to be non-empty (it now reverts config.json), "
        f"got empty={result.stdout!r}"
    )
