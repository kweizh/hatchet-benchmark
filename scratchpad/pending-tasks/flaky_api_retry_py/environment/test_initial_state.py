import os
import shutil
import socket
import time
from pathlib import Path

import pytest

PROJECT_DIR = "/home/user/project"
ENV_FILE = Path("/etc/hatchet.env")
ENV_WAIT_TIMEOUT_SEC = 180
COUNTER_FILE = Path("/var/lib/flaky/counter.txt")


def _load_env_from_file() -> None:
    """Best-effort reload of /etc/hatchet.env into os.environ.

    The container bootstraps Postgres + hatchet-lite and writes the API
    token into /etc/hatchet.env at startup. The Python .pth hook installed
    in the image normally loads this file automatically, but if this test
    is invoked before the bootstrap script finishes we wait briefly and
    then reload the env file ourselves.
    """
    if not ENV_FILE.exists():
        return
    try:
        text = ENV_FILE.read_text()
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ[key] = value


def _wait_for_env_file(timeout: float = ENV_WAIT_TIMEOUT_SEC) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ENV_FILE.exists():
            try:
                content = ENV_FILE.read_text()
            except OSError:
                content = ""
            if "HATCHET_CLIENT_TOKEN=" in content and len(content.strip()) > 80:
                _load_env_from_file()
                return True
        time.sleep(2)
    return False


def _wait_for_port(host: str, port: int, timeout: float = 60.0) -> int:
    deadline = time.time() + timeout
    last_result = -1
    while time.time() < deadline:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            last_result = sock.connect_ex((host, port))
        finally:
            sock.close()
        if last_result == 0:
            return 0
        time.sleep(2)
    return last_result


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_python_available():
    assert shutil.which("python") is not None, "python binary not found in PATH."


def test_hatchet_sdk_importable():
    try:
        import hatchet_sdk  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"hatchet-sdk should be importable but failed with: {exc!r}")


def test_requests_importable():
    try:
        import requests  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"requests should be importable but failed with: {exc!r}")


def test_pytest_importable():
    try:
        import pytest as _pytest  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive
        pytest.fail(f"pytest should be importable but failed with: {exc!r}")


def test_hatchet_bootstrap_complete():
    assert _wait_for_env_file(), (
        "The container bootstrap (Postgres + hatchet-lite + token generation) "
        "did not produce /etc/hatchet.env within "
        f"{ENV_WAIT_TIMEOUT_SEC} seconds."
    )


def test_hatchet_client_token_env_var_set():
    if not os.environ.get("HATCHET_CLIENT_TOKEN"):
        _wait_for_env_file()
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    assert token, (
        "HATCHET_CLIENT_TOKEN environment variable must be set so the SDK "
        "can authenticate against the local hatchet-lite engine."
    )


def test_hatchet_client_tls_strategy_none():
    if os.environ.get("HATCHET_CLIENT_TLS_STRATEGY") != "none":
        _wait_for_env_file()
    strategy = os.environ.get("HATCHET_CLIENT_TLS_STRATEGY", "")
    assert strategy == "none", (
        "HATCHET_CLIENT_TLS_STRATEGY must equal 'none' for the local "
        f"hatchet-lite engine (current value: {strategy!r})."
    )


def test_hatchet_grpc_port_reachable():
    # hatchet-lite exposes the gRPC API on 127.0.0.1:7077 inside the container.
    result = _wait_for_port("127.0.0.1", 7077, timeout=60)
    assert result == 0, (
        "Expected the local hatchet-lite gRPC port 7077 to be reachable, "
        f"but connect_ex returned {result}."
    )


def test_flaky_api_port_reachable():
    # The container also runs a local flaky HTTP API on 127.0.0.1:9001.
    result = _wait_for_port("127.0.0.1", 9001, timeout=60)
    assert result == 0, (
        "Expected the local flaky HTTP API on 127.0.0.1:9001 to be reachable, "
        f"but connect_ex returned {result}."
    )


def test_flaky_api_healthz_returns_200():
    # The flaky server exposes /healthz; this just confirms HTTP is alive.
    import requests

    deadline = time.time() + 60
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            resp = requests.get("http://127.0.0.1:9001/healthz", timeout=5)
            if resp.status_code == 200:
                return
            last_exc = RuntimeError(f"unexpected status {resp.status_code}")
        except Exception as exc:  # pragma: no cover - defensive
            last_exc = exc
        time.sleep(2)
    pytest.fail(
        f"Flaky HTTP server /healthz did not return 200 within 60s: {last_exc!r}"
    )


def test_flaky_counter_file_dir_exists():
    # The flaky server persists its global call counter to /var/lib/flaky/counter.txt.
    assert COUNTER_FILE.parent.is_dir(), (
        f"Expected the flaky-server counter directory {COUNTER_FILE.parent} to exist."
    )
