import os
import shutil
import socket

import pytest


PROJECT_DIR = "/home/user/myproject"


def test_hatchet_sdk_importable():
    try:
        import hatchet_sdk  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"hatchet_sdk package is not importable: {exc}")


def test_pydantic_importable():
    try:
        import pydantic  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"pydantic package is not importable: {exc}")


def test_pytest_available():
    assert shutil.which("pytest") is not None, "pytest binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."
    assert len(token) > 20, (
        "HATCHET_CLIENT_TOKEN looks too short to be a real Hatchet API token."
    )


def test_hatchet_tls_strategy_none():
    strategy = os.environ.get("HATCHET_CLIENT_TLS_STRATEGY", "")
    assert strategy == "none", (
        "HATCHET_CLIENT_TLS_STRATEGY must equal 'none' for the local hatchet-lite "
        f"server, got {strategy!r}."
    )


def test_hatchet_host_port_env_set():
    host_port = os.environ.get("HATCHET_CLIENT_HOST_PORT", "")
    assert host_port, "HATCHET_CLIENT_HOST_PORT environment variable is not set."
    assert ":" in host_port, (
        f"HATCHET_CLIENT_HOST_PORT must be of the form host:port, got {host_port!r}."
    )


def test_hatchet_grpc_endpoint_reachable():
    host_port = os.environ.get("HATCHET_CLIENT_HOST_PORT", "localhost:7077")
    host, _, port = host_port.partition(":")
    port = int(port or "7077")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        try:
            sock.connect((host, port))
        except OSError as exc:
            pytest.fail(
                f"Cannot reach Hatchet gRPC endpoint at {host}:{port}: {exc}"
            )
