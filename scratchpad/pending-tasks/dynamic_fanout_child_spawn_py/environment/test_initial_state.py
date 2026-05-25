import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 is not available on PATH."


def test_pip3_available():
    assert shutil.which("pip3") is not None, "pip3 is not available on PATH."


def test_hatchet_sdk_importable():
    result = subprocess.run(
        ["python3", "-c", "import hatchet_sdk"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Failed to import hatchet_sdk in python3. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_var_present():
    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN environment variable is not set."
    )


def test_hatchet_server_url_env_var_present():
    assert os.environ.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL environment variable is not set."
    )


def test_zealt_run_id_env_var_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
