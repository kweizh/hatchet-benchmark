import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} must exist before the task begins."
    )


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as exc:  # pragma: no cover - diagnostic
        raise AssertionError(
            "hatchet_sdk Python package must be importable (install via pip install hatchet-sdk)."
        ) from exc


def test_hatchet_client_token_env_var_set():
    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN environment variable must be set for the task to authenticate."
    )


def test_hatchet_server_url_env_var_set():
    assert os.environ.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL environment variable must be set so the SDK can reach the Hatchet server."
    )


def test_zealt_run_id_env_var_set():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID environment variable must be set so resource names can be made unique per run."
    )
