import os
import re
import shutil
import subprocess


PROJECT_DIR = "/home/user/hatchet-install"
LOG_FILE = os.path.join(PROJECT_DIR, "install.log")
# Matches a semver string like "0.86.29" or "v0.81.0" (optionally with pre-release/build suffix).
SEMVER_PATTERN = re.compile(r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?")


def test_hatchet_binary_on_path():
    """The Hatchet CLI must be installed and reachable through PATH."""
    binary_path = shutil.which("hatchet")
    assert binary_path is not None, (
        "Expected the `hatchet` CLI to be installed and discoverable on PATH, "
        "but `shutil.which('hatchet')` returned None."
    )
    assert os.path.isfile(binary_path), (
        f"`which hatchet` resolved to {binary_path}, but no file exists at that path."
    )
    assert os.access(binary_path, os.X_OK), (
        f"`hatchet` binary at {binary_path} is not executable."
    )


def test_hatchet_version_command_runs():
    """`hatchet --version` must exit 0 and print a semantic version string."""
    result = subprocess.run(
        ["hatchet", "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "Expected `hatchet --version` to exit with status 0, got "
        f"returncode={result.returncode}. stderr={result.stderr!r}"
    )
    combined_output = (result.stdout or "") + (result.stderr or "")
    match = SEMVER_PATTERN.search(combined_output)
    assert match is not None, (
        "Expected `hatchet --version` output to contain a semantic version string "
        f"(e.g. '0.86.29' or 'v0.81.0'), got: {combined_output!r}"
    )


def test_install_log_records_version():
    """The install log must capture the Hatchet version output."""
    assert os.path.isfile(LOG_FILE), (
        f"Expected install log file at {LOG_FILE} to exist."
    )
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    assert content.strip(), f"Install log file {LOG_FILE} is empty."
    assert SEMVER_PATTERN.search(content), (
        f"Expected {LOG_FILE} to contain a semantic version string "
        f"(e.g. '0.86.29' or 'v0.81.0'), got: {content!r}"
    )
