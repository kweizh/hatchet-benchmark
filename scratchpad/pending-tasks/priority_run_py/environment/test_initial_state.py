import os
import pytest


PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hatchet_sdk_importable():
    try:
        import hatchet_sdk  # noqa: F401
    except Exception as exc:  # pragma: no cover
        pytest.fail(f"hatchet_sdk Python package is not importable: {exc}")


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable must be set before the task starts."


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set before the task starts."
