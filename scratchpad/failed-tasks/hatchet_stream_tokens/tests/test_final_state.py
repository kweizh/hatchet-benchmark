import os
import subprocess
import time
import socket
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/app"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

@pytest.fixture(scope="module")
def setup_environment():
    hatchet_proc = None
    if not is_port_in_use(8888):
        # 1. Ensure Hatchet is running
        hatchet_proc = subprocess.Popen(
            ["/usr/local/bin/start-hatchet.sh"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
        time.sleep(10) # Wait for initialization
    
    # 2. Run the worker in the background
    worker_proc = subprocess.Popen(
        ["python3", "worker.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    time.sleep(5) # Wait for worker to register

    # 3. Run the client
    client_result = subprocess.run(
        ["python3", "client.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    yield client_result

    # Teardown
    import signal
    try:
        os.killpg(os.getpgid(worker_proc.pid), signal.SIGTERM)
    except Exception:
        pass
    
    if hatchet_proc:
        try:
            os.killpg(os.getpgid(hatchet_proc.pid), signal.SIGTERM)
        except Exception:
            pass

def test_client_execution_successful(setup_environment):
    client_result = setup_environment
    assert client_result.returncode == 0, \
        f"client.py failed with error: {client_result.stderr}"

def test_stream_log_content_with_amika(setup_environment):
    reason = "The task requires a Hatchet client to consume a stream and write the chunks to stream.log."
    truth = "Verify that the file /home/user/app/stream.log exists and contains the exact text 'Hatchet streaming is awesome!'."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_hatchet_stream_tokens"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
