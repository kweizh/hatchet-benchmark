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


def test_requests_importable():
    try:
        import requests  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"requests package is not importable: {exc}")


def test_pytest_available():
    assert shutil.which("pytest") is not None, "pytest binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hatchet_client_token_env_set():
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."
    assert len(token) > 20, "HATCHET_CLIENT_TOKEN looks too short to be a real token."


def test_hatchet_tls_strategy_none():
    strategy = os.environ.get("HATCHET_CLIENT_TLS_STRATEGY", "")
    assert strategy == "none", (
        f"HATCHET_CLIENT_TLS_STRATEGY must equal 'none' for the local hatchet-lite server, got {strategy!r}."
    )


def test_hatchet_host_port_env_set():
    host_port = os.environ.get("HATCHET_CLIENT_HOST_PORT", "")
    assert host_port, "HATCHET_CLIENT_HOST_PORT must be set for the worker to connect to hatchet-lite."


def test_hatchet_server_url_env_set():
    server_url = os.environ.get("HATCHET_CLIENT_SERVER_URL", "")
    assert server_url.startswith("http"), (
        f"HATCHET_CLIENT_SERVER_URL must be set to the hatchet-lite HTTP API base URL, got {server_url!r}."
    )


def test_hatchet_tenant_id_env_set():
    tenant_id = os.environ.get("HATCHET_CLIENT_TENANT_ID", "")
    assert tenant_id, (
        "HATCHET_CLIENT_TENANT_ID must be exported so the verifier can query the workers REST endpoint."
    )
    # UUID-ish minimum length sanity check
    assert len(tenant_id) >= 32, (
        f"HATCHET_CLIENT_TENANT_ID looks too short to be a real tenant UUID, got {tenant_id!r}."
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
            pytest.fail(f"Cannot reach Hatchet gRPC endpoint at {host}:{port}: {exc}")


def test_hatchet_http_api_reachable():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        try:
            sock.connect(("localhost", 8888))
        except OSError as exc:
            pytest.fail(f"Cannot reach Hatchet HTTP API on localhost:8888: {exc}")
