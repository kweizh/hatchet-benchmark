import os
import json
import time
import multiprocessing
from datetime import datetime
from hatchet_sdk import Hatchet

# Initialize Hatchet client
hatchet = Hatchet()

TRIGGERED_FILE = "/tmp/triggered.json"

@hatchet.task(name="on_user_created", on_events=["user:created"])
def on_user_created(workflow_input, context):
    print(f"Task triggered with payload: {workflow_input}")
    
    # Get the event payload as a dict
    if hasattr(workflow_input, 'model_dump'):
        event_payload = workflow_input.model_dump()
    else:
        event_payload = dict(workflow_input)
    
    # Prepare the record
    record = {
        "event_payload": event_payload,
        "received_at": datetime.now().isoformat()
    }
    
    # Write to /tmp/triggered.json
    with open(TRIGGERED_FILE, "w") as f:
        json.dump(record, f)
    
    print(f"Successfully wrote to {TRIGGERED_FILE}")
    return record

def run_worker():
    worker = hatchet.worker("test-worker", workflows=[on_user_created])
    worker.start()

def main():
    # 1. Remove any pre-existing /tmp/triggered.json file
    if os.path.exists(TRIGGERED_FILE):
        os.remove(TRIGGERED_FILE)
        print(f"Removed existing {TRIGGERED_FILE}")

    # 2. Start the Hatchet worker in the background
    worker_process = multiprocessing.Process(target=run_worker)
    worker_process.start()
    print("Started Hatchet worker in background")

    try:
        # 3. Wait long enough for the worker to register with Hatchet Cloud
        print("Waiting 15 seconds for worker registration...")
        time.sleep(15)

        # 4. Push an event
        run_id = os.getenv("ZEALT_RUN_ID", "default-run-id")
        event_key = "user:created"
        payload = {"user_id": f"abc-{run_id}"}
        
        print(f"Pushing event {event_key} with payload {payload}")
        hatchet.event.push(event_key, payload)

        # 5. Wait for the task to execute
        print("Waiting up to 60 seconds for task execution...")
        start_time = time.time()
        timeout = 60
        while time.time() - start_time < timeout:
            if os.path.exists(TRIGGERED_FILE):
                print(f"Found {TRIGGERED_FILE}! Task executed successfully.")
                break
            time.sleep(2)
        else:
            print("Timed out waiting for task execution.")

    finally:
        # 6. Exit cleanly (terminate worker)
        print("Cleaning up worker process...")
        worker_process.terminate()
        worker_process.join()
        print("Done.")

if __name__ == "__main__":
    main()
