import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as exc:  # pragma: no cover - assertion message handles failure
        raise AssertionError(
            f"hatchet_sdk Python package is not importable: {exc}"
        )


def test_hatchet_client_token_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
