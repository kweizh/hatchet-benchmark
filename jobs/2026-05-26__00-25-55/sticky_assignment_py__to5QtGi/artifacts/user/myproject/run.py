import os
import socket
import json
import time
import multiprocessing
from hatchet_sdk import Hatchet, StickyStrategy

# Read run-id from environment
RUN_ID = os.environ.get("ZEALT_RUN_ID", "default")
LOG_FILE = "/tmp/run_steps.log"

hatchet = Hatchet()

def log_step(step_name):
    worker_id = os.environ.get("WORKER_ID", "unknown")
    hostname = socket.gethostname()
    pid = os.getpid()
    line = f"step={step_name} worker_id={worker_id} hostname={hostname} pid={pid}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    return worker_id

# Define the workflow
workflow = hatchet.workflow(
    name=f"sticky-dag-{RUN_ID}",
    sticky=StickyStrategy.SOFT
)

@workflow.task(name="step_a")
def step_a(input, context):
    worker_id = log_step("step_a")
    return {"worker_id": worker_id}

@workflow.task(name="step_b", parents=[step_a])
def step_b(input, context):
    worker_id = log_step("step_b")
    return {"worker_id": worker_id}

@workflow.task(name="step_c", parents=[step_b])
def step_c(input, context):
    worker_id = log_step("step_c")
    return {"worker_id": worker_id}

def run_worker(worker_id):
    os.environ["WORKER_ID"] = worker_id
    # Each process needs its own Hatchet client
    worker_hatchet = Hatchet()
    worker = worker_hatchet.worker(f"worker-{worker_id}")
    worker.register_workflow(workflow)
    print(f"Starting worker {worker_id}...")
    worker.start()

def main():
    # Ensure log file is empty
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    # IDs for the two workers
    worker_a_id = f"worker-A-{RUN_ID}"
    worker_b_id = f"worker-B-{RUN_ID}"

    # Start two worker processes
    p1 = multiprocessing.Process(target=run_worker, args=(worker_a_id,))
    p2 = multiprocessing.Process(target=run_worker, args=(worker_b_id,))
    
    p1.start()
    p2.start()

    try:
        # Wait for workers to be ready
        print("Waiting for workers to start...")
        time.sleep(15)

        # Trigger the workflow
        print(f"Triggering workflow sticky-dag-{RUN_ID}...")
        workflow_run = workflow.run({})
        
        # Wait for completion
        print("Waiting for workflow completion...")
        
        max_wait = 120
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        break
            time.sleep(2)
        
        # Read worker IDs from log
        worker_ids = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    # step=step_a worker_id=worker-A-xxx hostname=... pid=...
                    parts = line.strip().split(" ")
                    w_id = None
                    for part in parts:
                        if part.startswith("worker_id="):
                            w_id = part.split("=")[1]
                            break
                    if w_id:
                        worker_ids.append(w_id)

        # Write result.json
        result = {"worker_ids": worker_ids}
        with open("/tmp/result.json", "w") as f:
            json.dump(result, f)
        
        print(f"Workflow finished. Worker IDs: {worker_ids}")

    finally:
        print("Terminating workers...")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()

if __name__ == "__main__":
    main()
