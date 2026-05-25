import importlib
import os
import shutil


PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_pip3_available():
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as exc:  # pragma: no cover - failure path
        raise AssertionError(
            f"hatchet_sdk Python package must be importable in the task environment, got: {exc!r}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} must exist before the task starts."
    )


def test_hatchet_client_token_env_set():
    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN must be set in the task environment so the worker can authenticate."
    )


def test_hatchet_server_url_env_set():
    assert os.environ.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL must be set in the task environment so the SDK can locate the server."
    )


def test_zealt_run_id_env_set():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID must be set for parallel-run isolation of workflow names and event keys."
    )
