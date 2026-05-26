import os
import shutil
import subprocess


PROJECT_DIR = "/home/user/quickstart-project"
HATCHET_PROFILES_PATH = os.path.expanduser("~/.hatchet/profiles.yaml")


def test_hatchet_cli_available_on_path():
    assert shutil.which("hatchet") is not None, (
        "The hatchet CLI binary was not found on PATH. "
        "It should be pre-installed by the Dockerfile."
    )


def test_hatchet_cli_runs():
    result = subprocess.run(
        ["hatchet", "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"hatchet --version exited with code {result.returncode}; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stdout.strip() != "", (
        "hatchet --version returned an empty version string."
    )


def test_hatchet_profile_preconfigured():
    assert os.path.isfile(HATCHET_PROFILES_PATH), (
        f"Expected a pre-configured Hatchet profile file at {HATCHET_PROFILES_PATH}, "
        "but it does not exist. The quickstart command requires at least one profile."
    )
    with open(HATCHET_PROFILES_PATH) as f:
        content = f.read()
    assert "profiles:" in content, (
        f"{HATCHET_PROFILES_PATH} does not contain a `profiles:` section."
    )


def test_target_project_dir_does_not_exist_yet():
    assert not os.path.exists(PROJECT_DIR), (
        f"The target project directory {PROJECT_DIR} already exists before the task starts. "
        "`hatchet quickstart` refuses to run when the directory already exists."
    )
