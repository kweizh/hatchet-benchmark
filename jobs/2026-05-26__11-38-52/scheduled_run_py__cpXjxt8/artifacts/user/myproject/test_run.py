import os
import json
import time
from datetime import datetime, timedelta, timezone
from hatchet_sdk import Hatchet
import threading

hatchet = Hatchet()

@hatchet.task(name="scheduled-hello")
def scheduled_hello(input_data, context):
    print("Inside task")
    print("type:", type(input_data))
    if hasattr(input_data, "model_dump"):
        print("dump:", input_data.model_dump())
    elif hasattr(input_data, "dict"):
        print("dict:", input_data.dict())
    else:
        print("dict cast:", dict(input_data))
    return {"status": "ok"}

def main():
    worker = hatchet.worker("scheduled-worker")
    worker.register_workflow(scheduled_hello)
    
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    print("Triggering scheduled run...")
    trigger_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    run = hatchet.scheduled.create("scheduled-hello", trigger_at, {"name": "test"}, {})
    time.sleep(8)
    
if __name__ == "__main__":
    main()
