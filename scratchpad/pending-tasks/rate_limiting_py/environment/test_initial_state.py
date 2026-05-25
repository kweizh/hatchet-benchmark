import importlib
import os
import socket

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hatchet_sdk_importable():
    try:
        importlib.import_module("hatchet_sdk")
    except ImportError as exc:  # pragma: no cover - failure path
        pytest.fail(f"hatchet_sdk Python package is not importable: {exc}")


def test_hatchet_client_token_env_present():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."


def test_hatchet_client_host_port_env_present():
    host_port = os.environ.get("HATCHET_CLIENT_HOST_PORT")
    assert host_port, "HATCHET_CLIENT_HOST_PORT environment variable is not set."


def test_hatchet_engine_reachable():
    host_port = os.environ.get("HATCHET_CLIENT_HOST_PORT", "")
    assert ":" in host_port, (
        f"HATCHET_CLIENT_HOST_PORT must be in '<host>:<port>' form, got {host_port!r}."
    )
    host, port_str = host_port.rsplit(":", 1)
    try:
        port = int(port_str)
    except ValueError:  # pragma: no cover - failure path
        pytest.fail(f"Invalid port in HATCHET_CLIENT_HOST_PORT: {host_port!r}.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        try:
            sock.connect((host, port))
        except OSError as exc:
            pytest.fail(
                f"Could not connect to Hatchet engine at {host}:{port}: {exc}."
            )
