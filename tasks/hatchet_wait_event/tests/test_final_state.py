import os
import subprocess
import time
import pytest
import json

PROJECT_DIR = "/home/user/myproject"

@pytest.fixture(scope="module")
def worker_process():
    process = subprocess.Popen(
        ["python3", "worker.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    time.sleep(5)  # Wait for worker to connect
    yield process
    import signal
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=10)

def test_event_confirmation(worker_process):
    # Write a temporary script to trigger workflow and push event
    script = """
from hatchet_sdk import Hatchet
import time

def main():
    hatchet = Hatchet()
    workflow_run = hatchet.admin.run_workflow("OrderWorkflow", {})
    
    # Wait a bit for it to start
    time.sleep(2)
    
    # Push the event
    hatchet.client.event.push("user:confirm", {})
    
    # Wait for completion
    result = workflow_run.result()
    print(result)

if __name__ == "__main__":
    main()
"""
    script_path = os.path.join(PROJECT_DIR, "test_confirm.py")
    with open(script_path, "w") as f:
        f.write(script)
    
    result = subprocess.run(
        ["python3", "test_confirm.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Trigger script failed: {result.stderr}"
    assert "confirmed" in result.stdout or "confirmed" in result.stderr, \
        f"Expected 'confirmed' status, got: {result.stdout} {result.stderr}"

def test_event_timeout(worker_process):
    # Write a temporary script to trigger workflow and wait for timeout
    script = """
from hatchet_sdk import Hatchet

def main():
    hatchet = Hatchet()
    workflow_run = hatchet.admin.run_workflow("OrderWorkflow", {})
    
    # Wait for completion (should take 5 minutes)
    result = workflow_run.result()
    print(result)

if __name__ == "__main__":
    main()
"""
    script_path = os.path.join(PROJECT_DIR, "test_timeout.py")
    with open(script_path, "w") as f:
        f.write(script)
    
    start_time = time.time()
    result = subprocess.run(
        ["python3", "test_timeout.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start_time
    
    assert result.returncode == 0, f"Trigger script failed: {result.stderr}"
    assert "cancelled" in result.stdout or "cancelled" in result.stderr, \
        f"Expected 'cancelled' status, got: {result.stdout} {result.stderr}"
    assert elapsed >= 290, f"Task should have waited ~5 minutes, but finished in {elapsed} seconds"
