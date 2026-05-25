import importlib
import os
import shutil
import socket
import subprocess

import urllib.request

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 not available in PATH."


def test_hatchet_sdk_importable():
    mod = importlib.import_module("hatchet_sdk")
    assert mod is not None, "hatchet_sdk Python package is not importable."


def test_requests_importable():
    mod = importlib.import_module("requests")
    assert mod is not None, "requests Python package is not importable."


def test_hatchet_client_token_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."


def test_postgres_running():
    result = subprocess.run(
        ["pg_isready", "-h", "127.0.0.1", "-p", "5432"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Local Postgres is not ready: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_hatchet_engine_grpc_listening():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect(("127.0.0.1", 7077))
    except Exception as e:
        raise AssertionError(f"Could not connect to Hatchet engine on 127.0.0.1:7077: {e}")
    finally:
        s.close()


def test_mock_llm_listening_on_9100():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect(("127.0.0.1", 9100))
    except Exception as e:
        raise AssertionError(f"Mock LLM server is not listening on 127.0.0.1:9100: {e}")
    finally:
        s.close()


def test_mock_llm_health_endpoint():
    """The mock LLM exposes a /health endpoint that returns 200 OK."""
    req = urllib.request.Request("http://127.0.0.1:9100/health", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200, f"Mock LLM /health returned status {resp.status}, expected 200."
    except Exception as e:
        raise AssertionError(f"Could not query mock LLM /health on http://127.0.0.1:9100/health: {e}")
