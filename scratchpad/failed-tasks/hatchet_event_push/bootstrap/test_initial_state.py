import os
import subprocess

def test_docker_installed():
    """Verify Docker is installed and functional."""
    result = subprocess.run(["docker", "--version"], capture_output=True)
    assert result.returncode == 0, f"Docker is not installed: {result.stderr}"

def test_hatchet_cli_installed():
    """Verify Hatchet CLI is installed."""
    result = subprocess.run(["hatchet", "--version"], capture_output=True)
    assert result.returncode == 0, f"Hatchet CLI is not installed: {result.stderr}"

def test_python_sdk_installed():
    """Verify Hatchet Python SDK is installed."""
    result = subprocess.run(["python3", "-c", "import hatchet_sdk"], capture_output=True)
    assert result.returncode == 0, f"Hatchet Python SDK is not installed: {result.stderr}"
