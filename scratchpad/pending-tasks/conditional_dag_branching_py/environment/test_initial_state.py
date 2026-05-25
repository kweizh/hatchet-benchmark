import os
import importlib

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as exc:  # pragma: no cover
        raise AssertionError(
            f"hatchet-sdk Python package is not importable: {exc}"
        )


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set in the task "
        "environment."
    )


def test_hatchet_server_url_env_present():
    url = os.environ.get("HATCHET_SERVER_URL")
    assert url, (
        "HATCHET_SERVER_URL environment variable must be set in the task "
        "environment."
    )


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set in the task environment."
    )
