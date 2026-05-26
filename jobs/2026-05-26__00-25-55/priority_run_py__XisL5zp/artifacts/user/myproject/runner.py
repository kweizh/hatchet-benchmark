import os
import time
import subprocess
import signal
from hatchet_sdk import Hatchet
from workflow import TASK_NAME, LOG_FILE, ZEALT_RUN_ID, workflow as workflow_def

hatchet = Hatchet()

def main():
    # 1. Truncate (create fresh) the log file
    with open(LOG_FILE, "w") as f:
        pass

    # 2. Starts the worker in a background process
    print(f"Starting worker for {TASK_NAME}...")
    with open("worker_stdout.log", "w") as out, open("worker_stderr.log", "w") as err:
        worker_proc = subprocess.Popen(
            ["python3", "/home/user/myproject/workflow.py"],
            stdout=out,
            stderr=err,
            text=True
        )
    
    # Give the worker a moment to start and register
    time.sleep(15)

    print(f"Submitting tasks for {TASK_NAME}...")

    # 3. Submits 5 task runs back-to-back with no waiting between submissions
    # First: 3 runs at priority 1 (low)
    # Then: 2 runs at priority 3 (high)
    
    # Priority 1 runs
    for i in range(3):
        print(f"Enqueuing priority 1 run {i+1}")
        workflow_def.run(input={}, priority=1, wait_for_result=False)
        
    # Priority 3 runs
    for i in range(2):
        print(f"Enqueuing priority 3 run {i+1}")
        workflow_def.run(input={}, priority=3, wait_for_result=False)

    # 4. Waits for all 5 runs to complete (synchronously block until done)
    print("Waiting for runs to complete...")
    
    completed_count = 0
    start_wait = time.time()
    timeout = 60 # 60 seconds timeout
    
    while completed_count < 5 and (time.time() - start_wait) < timeout:
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                    completed_count = len([l for l in lines if l.strip()])
                    if completed_count > 0:
                        print(f"Progress: {completed_count}/5 runs completed...")
        except Exception as e:
            print(f"Error reading log: {e}")
        
        if completed_count < 5:
            time.sleep(2)
            
    if completed_count < 5:
        print(f"Timed out waiting for completion. Only {completed_count} runs finished.")
        if os.path.exists("worker_stderr.log"):
            with open("worker_stderr.log", "r") as f:
                print(f"Worker stderr:\n{f.read()}")
        if os.path.exists("worker_stdout.log"):
            with open("worker_stdout.log", "r") as f:
                print(f"Worker stdout:\n{f.read()}")
    else:
        print("All 5 runs completed.")

    # 5. Stops the worker cleanly and exits
    print("Stopping worker...")
    worker_proc.send_signal(signal.SIGINT)
    try:
        worker_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        worker_proc.kill()
    
    print("Runner exiting.")

if __name__ == "__main__":
    main()
