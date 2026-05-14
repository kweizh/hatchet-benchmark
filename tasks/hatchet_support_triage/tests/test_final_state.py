import os
import subprocess
import time
import pytest

PROJECT_DIR = "/home/user/support-agent"
WORKER_FILE = os.path.join(PROJECT_DIR, "worker.py")
TEST_SCRIPT = os.path.join(PROJECT_DIR, "test_run.py")

@pytest.fixture(scope="module")
def start_worker():
    assert os.path.isfile(WORKER_FILE), f"worker.py not found at {WORKER_FILE}"
    
    # Start the worker
    process = subprocess.Popen(
        ["python3", "worker.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for the worker to connect
    time.sleep(5)
    
    yield
    
    # Shut down the worker
    import signal
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=10)

def test_amika_validation():
    """Use the amika CLI to do the validation in final tests as requested."""
    try:
        result = subprocess.run(
            ["amika", "sandbox", "agent-send", "local", "Verify the Hatchet support agent workflow executed correctly"],
            capture_output=True,
            text=True
        )
        print(f"Amika validation output: {result.stdout}")
    except FileNotFoundError:
        pytest.skip("amika CLI not found, skipping amika validation")

def test_workflow_execution(start_worker):
    """Test the workflow execution by triggering it via a script."""
    
    test_script_content = """
import sys
import time
from hatchet_sdk import Hatchet
from worker import support_agent, SupportTicketInput

def main():
    hatchet_client = Hatchet()
    
    print("Testing resolved path...")
    ticket1 = SupportTicketInput(
        ticket_id="t1",
        customer_email="test@example.com",
        subject="login issue",
        body="broken"
    )
    # Start workflow without waiting
    ref1 = support_agent.run_no_wait(ticket1)
    
    # Wait a bit for the workflow to reach the wait condition
    time.sleep(1)
    
    # Push customer reply event
    hatchet_client.event.push(
        "customer:reply",
        {"message": "fixed it"},
        scope="t1"
    )
    
    # Wait for result
    res1 = ref1.result()
    assert res1["status"] == "resolved", f"Expected resolved, got {res1}"
    assert res1["triage_category"] == "account", f"Expected account, got {res1}"
    assert res1["triage_priority"] == "medium", f"Expected medium, got {res1}"
    
    print("Testing escalated path...")
    ticket2 = SupportTicketInput(
        ticket_id="t2",
        customer_email="test2@example.com",
        subject="billing issue",
        body="charge"
    )
    # Start workflow and wait for timeout
    ref2 = support_agent.run_no_wait(ticket2)
    res2 = ref2.result()
    
    assert res2["status"] == "escalated", f"Expected escalated, got {res2}"
    assert res2["triage_category"] == "billing", f"Expected billing, got {res2}"
    assert res2["triage_priority"] == "low", f"Expected low, got {res2}"
    
    print("ALL_TESTS_PASSED")

if __name__ == "__main__":
    main()
"""
    
    with open(TEST_SCRIPT, "w") as f:
        f.write(test_script_content)
        
    result = subprocess.run(
        ["python3", "test_run.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Test script failed: {result.stderr}\nSTDOUT: {result.stdout}"
    assert "ALL_TESTS_PASSED" in result.stdout, f"Test script did not complete successfully: {result.stdout}"
