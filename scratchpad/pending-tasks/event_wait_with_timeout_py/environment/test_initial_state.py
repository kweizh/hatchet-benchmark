import os
import shutil
import importlib


PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 is not available in PATH."


def test_pip3_available():
    assert shutil.which("pip3") is not None, "pip3 is not available in PATH."


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except Exception as exc:  # pragma: no cover - failure path
        raise AssertionError(
            f"Expected hatchet_sdk Python package to be importable, but got: {exc!r}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task runs."
    )


def test_hatchet_env_vars_present():
    assert os.environ.get("HATCHET_CLIENT_TOKEN"), (
        "HATCHET_CLIENT_TOKEN must be set in the environment so the task can connect to Hatchet."
    )
    assert os.environ.get("HATCHET_SERVER_URL"), (
        "HATCHET_SERVER_URL must be set in the environment so the task can connect to Hatchet."
    )


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID must be set so the task can scope its workflow/event names."
