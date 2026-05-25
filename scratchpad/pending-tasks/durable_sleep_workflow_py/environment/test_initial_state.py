import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    import shutil
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_pip3_available():
    import shutil
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except ImportError as e:
        raise AssertionError(
            f"hatchet_sdk Python package is not importable: {e}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set so the task "
        "can connect to a real Hatchet server."
    )


def test_hatchet_server_url_env_set():
    url = os.environ.get("HATCHET_SERVER_URL")
    assert url, (
        "HATCHET_SERVER_URL environment variable must be set so the task "
        "can connect to a real Hatchet server."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set so the task can "
        "build a unique workflow name."
    )
