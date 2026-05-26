import os
import json
import threading
import time
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

@hatchet.task(
    name="flaky_task",
    retries=3,
    backoff_factor=2,
    backoff_max_seconds=10
)
def flaky_task(input_data: dict, context: Context) -> dict:
    attempts_file = "/tmp/attempts.txt"
    try:
        with open(attempts_file, "r") as f:
            attempts = int(f.read().strip())
    except FileNotFoundError:
        attempts = 0
        
    attempts += 1
    
    with open(attempts_file, "w") as f:
        f.write(str(attempts))
        
    if attempts < 3:
        raise Exception(f"Flaky task failed on attempt {attempts}")
        
    return {"status": "success", "attempt": attempts}

def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "default")
    worker_name = f"task-retries-worker-{run_id}"
    
    attempts_file = "/tmp/attempts.txt"
    if os.path.exists(attempts_file):
        os.remove(attempts_file)
        
    worker = hatchet.worker(worker_name)
    worker.register_workflow(flaky_task)
    
    # Start worker in a separate thread
    # Note: worker.start() is blocking. We can also use worker.start_async() if we use asyncio, 
    # but threading is fine.
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    # Wait a bit for worker to be ready (registering to Hatchet Cloud)
    time.sleep(3)
    
    # Trigger the task and wait for it
    try:
        # The run method returns the result. It block until the task is done (or fails).
        print("Triggering task...")
        result = flaky_task.run({})
        print(f"Task result: {result}")
        
        # If result is a pydantic model, convert to dict
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        elif hasattr(result, "dict"):
            result_dict = result.dict()
        else:
            result_dict = result
            
        with open("/tmp/result.json", "w") as f:
            json.dump(result_dict, f)
            
    except Exception as e:
        print(f"Run failed: {e}")
        
    print("Stopping worker...")
    # worker.stop() or similar? Wait, hatchet worker might not have stop() method.
    # Let's check if worker has a stop method.
    if hasattr(worker, 'stop'):
        worker.stop()
    elif hasattr(worker, 'exit'):
        worker.exit()

if __name__ == "__main__":
    main()
