import os
import pytest

PROJECT_DIR = "/home/user/project"

def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hatchet_sdk_installed():
    try:
        import hatchet_sdk
    except ImportError:
        pytest.fail("hatchet-sdk Python package is not installed.")

def test_hatchet_client_token_env_var():
    assert "HATCHET_CLIENT_TOKEN" in os.environ, "HATCHET_CLIENT_TOKEN environment variable is not set."
