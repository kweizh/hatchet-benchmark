import os

PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    try:
        import hatchet_sdk  # noqa: F401
    except Exception as e:
        raise AssertionError(
            f"hatchet-sdk Python package is not importable in the task environment: {e}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist in the initial environment."
    )


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set in the initial environment "
        "so the runner can authenticate against Hatchet Cloud."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set so the worker name can be derived "
        "as ai-agent-loop-worker-${ZEALT_RUN_ID}."
    )
