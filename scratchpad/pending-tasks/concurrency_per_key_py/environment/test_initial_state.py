import os

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    import importlib
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as exc:
        raise AssertionError(
            f"hatchet_sdk Python package is not importable: {exc!r}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set with a real "
        "Hatchet Cloud token for the worker/client to authenticate."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set so the task can scope "
        "the registered Hatchet task name per grader trial."
    )


def test_runs_log_absent_initially():
    # The executor's runner is expected to CREATE /tmp/runs.log. It should not
    # exist yet in the initial environment.
    assert not os.path.exists("/tmp/runs.log"), (
        "/tmp/runs.log already exists before the task runs; the initial "
        "environment must start clean."
    )
