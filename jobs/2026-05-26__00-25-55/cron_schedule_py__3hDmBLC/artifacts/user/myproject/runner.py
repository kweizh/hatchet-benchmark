import os
import time
import multiprocessing
from datetime import datetime, timezone
from hatchet_sdk import Hatchet

# 1. Read ZEALT_RUN_ID from environment
zealt_run_id = os.getenv("ZEALT_RUN_ID")
if not zealt_run_id:
    raise ValueError("ZEALT_RUN_ID environment variable is not set")

# Initialize Hatchet client
hatchet = Hatchet()

# Define the heartbeat task using hatchet.task (Standalone task)
# Let's try the simplest V1 standalone task pattern
@hatchet.task(name=f"heartbeat-{zealt_run_id}")
def heartbeat(input, context):
    # Requirement: append timestamp in ISO 8601 format to /tmp/heartbeats.log
    timestamp = datetime.now(timezone.utc).isoformat()
    with open("/tmp/heartbeats.log", "a") as f:
        f.write(f"{timestamp}\n")
    print(f"Heartbeat at {timestamp}")
    return {"status": "success", "timestamp": timestamp}

def run_worker():
    # Re-initialize hatchet in the child process
    hatchet_worker = Hatchet()
    worker = hatchet_worker.worker(f"hb-worker-{zealt_run_id}")
    # standalones are registered with register_workflow in V1
    worker.register_workflow(heartbeat)
    worker.start()

def main():
    # 3. Start Hatchet worker in a SUBPROCESS
    worker_proc = multiprocessing.Process(target=run_worker)
    worker_proc.start()
    print("Worker started in subprocess")
    
    # Wait for registration to propagate
    print("Waiting for workflow registration (30s)...")
    time.sleep(30)

    # 2. Programmatically register a cron trigger
    # Cron name: hb-cron-${ZEALT_RUN_ID}
    # Expression: * * * * *
    cron_name = f"hb-cron-{zealt_run_id}"
    workflow_name = f"heartbeat-{zealt_run_id}"
    
    print(f"Creating cron trigger: {cron_name} for workflow: {workflow_name}")
    
    # Use hatchet.cron.create for programmatic cron
    cron_trigger = hatchet.cron.create(
        workflow_name=workflow_name,
        cron_name=cron_name,
        expression="* * * * *",
        input={},
        additional_metadata={}
    )
    
    cron_id = cron_trigger.metadata.id
    print(f"Cron trigger created with ID: {cron_id}")

    # 4. Keep the worker running for approximately 75 seconds
    print("Waiting 75 seconds for cron to fire...")
    time.sleep(75)

    # 5. Shut down the worker
    print("Terminating worker subprocess...")
    worker_proc.terminate()
    worker_proc.join()

    # 6. Delete the cron trigger
    print(f"Deleting cron trigger: {cron_id}")
    hatchet.cron.delete(cron_id=cron_id)
    print("Cron trigger deleted")

    # 7. Exit
    print("Done")

if __name__ == "__main__":
    main()
