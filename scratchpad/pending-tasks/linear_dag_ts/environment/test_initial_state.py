import os
import re
import shutil
import socket
import time

import pytest

PROJECT_DIR = "/home/user/myproject"
HATCHET_ENV_FILE = "/etc/hatchet.env"
HATCHET_API_HOST = "localhost"
HATCHET_API_PORT = 8888
HATCHET_GRPC_PORT = 7077


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(host, port, timeout=1.0):
            return True
        time.sleep(1.0)
    return False


def _read_env_file() -> dict:
    env: dict = {}
    if not os.path.isfile(HATCHET_ENV_FILE):
        return env
    pattern = re.compile(r"^\s*(?:export\s+)?([A-Z0-9_]+)=(.*)$")
    with open(HATCHET_ENV_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            match = pattern.match(line)
            if not match:
                continue
            key, value = match.group(1), match.group(2).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            env[key] = value
    return env


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_node_binary_available():
    assert shutil.which("node") is not None, (
        "Node.js runtime ('node') was not found in PATH. The task requires Node.js (LTS)."
    )


def test_npm_binary_available():
    assert shutil.which("npm") is not None, (
        "'npm' was not found in PATH. The task requires npm for installing the TypeScript SDK."
    )


def test_python3_available():
    assert shutil.which("python3") is not None, (
        "'python3' was not found in PATH. The verifier requires Python 3 with the Hatchet SDK."
    )


def test_python_hatchet_sdk_importable():
    pytest.importorskip(
        "hatchet_sdk",
        reason="Python 'hatchet_sdk' package must be installed for verification.",
    )


def test_hatchet_api_reachable():
    assert _wait_for_port(HATCHET_API_HOST, HATCHET_API_PORT, timeout=120.0), (
        f"Hatchet API is not reachable at {HATCHET_API_HOST}:{HATCHET_API_PORT}. "
        "The Hatchet Lite server must be running before the task starts."
    )


def test_hatchet_grpc_reachable():
    assert _wait_for_port(HATCHET_API_HOST, HATCHET_GRPC_PORT, timeout=120.0), (
        f"Hatchet gRPC endpoint is not reachable at {HATCHET_API_HOST}:{HATCHET_GRPC_PORT}. "
        "The Hatchet engine must accept gRPC connections from SDK workers."
    )


def test_hatchet_env_file_has_token():
    # The container startup script writes the real client token to /etc/hatchet.env so
    # any subsequent bash session (via BASH_ENV) can authenticate against the engine.
    # Poll for up to 120 seconds because the token is minted after the engine boots.
    deadline = time.time() + 120.0
    env: dict = {}
    while time.time() < deadline:
        env = _read_env_file()
        if env.get("HATCHET_CLIENT_TOKEN"):
            break
        time.sleep(2.0)
    assert env.get("HATCHET_CLIENT_TOKEN"), (
        f"{HATCHET_ENV_FILE} must contain a non-empty HATCHET_CLIENT_TOKEN written by "
        "/usr/local/bin/start-hatchet.sh at container startup."
    )
    assert env.get("HATCHET_CLIENT_TLS_STRATEGY") == "none", (
        f"{HATCHET_ENV_FILE} must set HATCHET_CLIENT_TLS_STRATEGY=none so SDK clients "
        "can talk to the local engine without TLS."
    )
