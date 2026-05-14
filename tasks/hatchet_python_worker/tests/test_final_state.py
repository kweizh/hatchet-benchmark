import os
import subprocess
import time
import json
import signal
import pytest

PROJECT_DIR = "/home/user/hatchet-worker"

@pytest.fixture(scope="module")
def start_worker():
    # Start the worker
    process = subprocess.Popen(
        ["python3", "worker.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for the worker to connect and be ready
    time.sleep(10)
    
    yield
    
    # Shut down the worker
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=10)

def test_worker_processes_event(start_worker):
    """Priority 1/3: Push event via Hatchet SDK and check output file."""
    # Create a temporary script to push the event
    push_script = os.path.join(PROJECT_DIR, "push_event_test.py")
    with open(push_script, "w") as f:
        f.write('''
from hatchet_sdk import Hatchet
import sys
import json

try:
    hatchet = Hatchet()
    hatchet.event.push("user:create", {"user_id": "123", "email": "test@example.com"})
    print("Event pushed successfully")
except Exception as e:
    print(f"Error pushing event: {e}", file=sys.stderr)
    sys.exit(1)
''')
    
    # Run the push script
    result = subprocess.run(
        ["python3", "push_event_test.py"],
        capture_output=True, text=True, cwd=PROJECT_DIR
    )
    assert result.returncode == 0, f"Failed to push event: {result.stderr}"
    
    # Wait for the worker to process the event
    time.sleep(15)
    
    # Check the output file
    output_file = os.path.join(PROJECT_DIR, "output.json")
    assert os.path.isfile(output_file), f"Output file {output_file} was not created by the worker."
    
    with open(output_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            pytest.fail(f"Output file {output_file} does not contain valid JSON.")
            
    assert data.get("user_id") == "123", f"Expected user_id '123' in output, got: {data.get('user_id')}"
    assert data.get("email") == "test@example.com", f"Expected email 'test@example.com' in output, got: {data.get('email')}"
