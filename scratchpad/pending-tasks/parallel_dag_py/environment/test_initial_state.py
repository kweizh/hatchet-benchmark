import os

import pytest


PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    """The hatchet-sdk Python package must be importable."""
    try:
        import hatchet_sdk  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"hatchet_sdk is not importable: {exc!r}")


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task runs."
    )


def test_hatchet_client_token_env_var_is_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set so the SDK can "
        "authenticate against Hatchet Cloud."
    )


def test_result_file_not_yet_created():
    """The /tmp/result.json file must not exist before the task runs."""
    assert not os.path.exists("/tmp/result.json"), (
        "/tmp/result.json must not exist before the task is executed; it is the "
        "agent's responsibility to create it."
    )
