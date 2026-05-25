import os
import importlib

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as e:
        raise AssertionError(
            f"The hatchet-sdk Python package must be importable (failed: {e})."
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token is not None and token != "", (
        "Environment variable HATCHET_CLIENT_TOKEN must be set for Hatchet Cloud authentication."
    )
