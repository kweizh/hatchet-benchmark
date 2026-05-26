import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    try:
        import hatchet_sdk  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"hatchet-sdk Python package is not importable: {exc!r}")


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_var_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set so the task "
        "can authenticate to Hatchet Cloud."
    )
