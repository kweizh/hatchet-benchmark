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
    except Exception as e:  # noqa: BLE001
        raise AssertionError(
            f"hatchet_sdk Python package is not importable: {e!r}"
        )


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable is not set; "
        "Hatchet Cloud authentication will fail."
    )
