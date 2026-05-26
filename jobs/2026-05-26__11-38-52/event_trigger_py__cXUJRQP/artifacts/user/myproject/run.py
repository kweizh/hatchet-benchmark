import os
import json
import time
import multiprocessing
from datetime import datetime, timezone
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

@hatchet.task(name="on_user_created", on_events=["user:created"])
def on_user_created(input_data: dict, context: Context):
    # Depending on pydantic version, it might be dict or model.
    # Let's try to convert it to dict if it's a model
    if hasattr(input_data, "model_dump"):
        payload = input_data.model_dump()
    elif hasattr(input_data, "dict"):
        payload = input_data.dict()
    else:
        payload = dict(input_data)
        
    output = {
        "event_payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    with open("/tmp/triggered.json", "w") as f:
        json.dump(output, f)

def run_worker():
    worker = hatchet.worker("test-worker", workflows=[on_user_created])
    worker.start()

def main():
    if os.path.exists("/tmp/triggered.json"):
        os.remove("/tmp/triggered.json")

    worker_process = multiprocessing.Process(target=run_worker)
    worker_process.start()

    print("Waiting for worker to register...")
    time.sleep(5)

    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    event_payload = {"user_id": f"abc-{run_id}"}
    print(f"Pushing event with payload: {event_payload}")
    hatchet.event.push("user:created", event_payload)

    print("Waiting for task to execute...")
    for _ in range(60):
        if os.path.exists("/tmp/triggered.json"):
            print("File /tmp/triggered.json found!")
            break
        time.sleep(1)
    
    worker_process.terminate()
    worker_process.join()
    print("Exiting.")

if __name__ == "__main__":
    main()
