import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    """The `hatchet-sdk` Python package must be importable in the initial environment."""
    try:
        import hatchet_sdk  # noqa: F401
    except ImportError as exc:  # pragma: no cover - defensive
        pytest.fail(f"hatchet_sdk Python package is not importable: {exc}")


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task begins."
    )


def test_hatchet_client_token_env_var_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set so the agent can "
        "authenticate to Hatchet Cloud."
    )


def test_zealt_run_id_env_var_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set so the agent can derive "
        "a parallel-safe cron trigger name."
    )


def test_heartbeats_log_not_yet_created():
    """The /tmp/heartbeats.log file is created BY the task; it must not pre-exist."""
    assert not os.path.exists("/tmp/heartbeats.log"), (
        "/tmp/heartbeats.log must not exist before the task runs; it is produced by "
        "the cron-fired heartbeat task."
    )
