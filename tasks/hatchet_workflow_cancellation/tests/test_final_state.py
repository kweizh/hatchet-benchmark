import os
import subprocess
import time
import pytest

PROJECT_DIR = "/home/user/myproject"

def test_workflow_cancellation():
    # 1. Start worker in the background
    worker_proc = subprocess.Popen(
        ["python3", "worker.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    try:
        # 2. Wait for worker to connect
        time.sleep(5)
        
        # 3. Run trigger script
        trigger_result = subprocess.run(
            ["python3", "trigger.py"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        assert trigger_result.returncode == 0, f"trigger.py failed: {trigger_result.stderr}"
        
        # 4. Wait for cancellation to propagate
        time.sleep(5)
        
        # 5. Read run_id from file
        run_id_file = os.path.join(PROJECT_DIR, "run_id.txt")
        assert os.path.isfile(run_id_file), f"{run_id_file} does not exist."
        
        with open(run_id_file, "r") as f:
            run_id = f.read().strip()
            
        assert run_id, "run_id.txt is empty."
        
        # 6. Verify using Hatchet SDK
        check_script = f"""
from hatchet_sdk import Hatchet
hatchet = Hatchet()
status = hatchet.runs.get_status("{run_id}")
print(str(status))
"""
        check_script_path = os.path.join(PROJECT_DIR, "check_status.py")
        with open(check_script_path, "w") as f:
            f.write(check_script)
            
        status_result = subprocess.run(
            ["python3", "check_status.py"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        assert status_result.returncode == 0, f"Failed to check status: {status_result.stderr}"
        
        status = status_result.stdout.strip().upper()
        assert "CANCELLED" in status, f"Expected status to contain CANCELLED, got: {status}"
        
    finally:
        # Cleanup: Kill worker process group
        import signal
        try:
            os.killpg(os.getpgid(worker_proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        worker_proc.wait(timeout=5)
