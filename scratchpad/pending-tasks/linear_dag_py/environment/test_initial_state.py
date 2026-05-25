import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    assert importlib.util.find_spec("hatchet_sdk") is not None, (
        "The hatchet_sdk Python package is not installed in the environment."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "Expected the HATCHET_CLIENT_TOKEN environment variable to be set so the agent can authenticate to Hatchet Cloud."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "Expected the ZEALT_RUN_ID environment variable to be set so the workflow name can be made unique per run."
    )


def test_result_file_not_yet_present():
    assert not os.path.exists("/tmp/result.json"), (
        "Expected /tmp/result.json to not exist before the task is executed."
    )
