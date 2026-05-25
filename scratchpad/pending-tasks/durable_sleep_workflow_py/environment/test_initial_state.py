import importlib
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 not available in PATH."


def test_hatchet_sdk_importable():
    mod = importlib.import_module("hatchet_sdk")
    assert mod is not None, "hatchet_sdk Python package is not importable."


def test_hatchet_client_token_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."


def test_postgres_running():
    # The container provides a local Postgres instance for the Hatchet engine.
    result = subprocess.run(
        ["pg_isready", "-h", "127.0.0.1", "-p", "5432"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Local Postgres is not ready: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_hatchet_engine_grpc_listening():
    # Hatchet engine should be listening on its default gRPC port 7077 inside the container.
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect(("127.0.0.1", 7077))
    except Exception as e:
        raise AssertionError(f"Could not connect to Hatchet engine on 127.0.0.1:7077: {e}")
    finally:
        s.close()
