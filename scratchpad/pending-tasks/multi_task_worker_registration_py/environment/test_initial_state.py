import os
import shutil


PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_pip3_available():
    assert shutil.which("pip3") is not None, "pip3 binary not found in PATH."


def test_hatchet_sdk_importable():
    try:
        import hatchet_sdk  # noqa: F401
    except Exception as exc:  # pragma: no cover - failure path
        raise AssertionError(
            f"Failed to import hatchet_sdk Python package: {exc}"
        )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_var_set():
    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN environment variable must be set to connect to "
        "the Hatchet server."
    )


def test_hatchet_server_url_env_var_set():
    assert os.environ.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL environment variable must be set to point at the "
        "Hatchet server."
    )


def test_zealt_run_id_env_var_set():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID environment variable must be set to scope task names."
    )
