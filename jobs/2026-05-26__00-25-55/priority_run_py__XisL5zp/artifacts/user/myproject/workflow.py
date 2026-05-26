import os
import time
from hatchet_sdk import Hatchet, Context
from dotenv import load_dotenv

load_dotenv()

hatchet = Hatchet()

ZEALT_RUN_ID = os.getenv("ZEALT_RUN_ID", "default")
TASK_NAME = f"prio-task-{ZEALT_RUN_ID}"
LOG_FILE = f"/tmp/prio_log_{ZEALT_RUN_ID}.txt"

workflow = hatchet.workflow(name=TASK_NAME, default_priority=1)

@workflow.task()
def step1(context: Context):
    # 1. Read the effective priority of the current run from the context
    try:
        priority = context.workflow_run_priority()
    except Exception:
        # Fallback
        priority = getattr(context.action, 'workflow_run_priority', 1)
        
    # 2. Compute the current epoch time in milliseconds (integer)
    epoch_ms = int(time.time() * 1000)
    
    # 3. Append exactly one line to the log file in the format <priority> <epoch_ms>\n
    with open(LOG_FILE, "a") as f:
        f.write(f"{priority} {epoch_ms}\n")
    
    # 4. Sleep for approximately 2 seconds
    time.sleep(2)
    
    return {"status": "success"}

def run_worker():
    # Using slots=1 as requested
    worker = hatchet.worker(f"worker-{ZEALT_RUN_ID}", slots=1)
    worker.register_workflow(workflow)
    worker.start()

if __name__ == "__main__":
    run_worker()
