import os
import json
import time
import threading
import multiprocessing
from hatchet_sdk import Hatchet
from dotenv import load_dotenv

load_dotenv()

hatchet = Hatchet()

@hatchet.task(
    retries=3,
    backoff_factor=2,
    backoff_max_seconds=10
)
def flaky_task(workflow_input, context):
    attempts_file = "/tmp/attempts.txt"
    
    # Read current attempt count
    if not os.path.exists(attempts_file):
        attempts = 0
    else:
        with open(attempts_file, "r") as f:
            try:
                attempts = int(f.read().strip())
            except ValueError:
                attempts = 0
    
    # Increment counter
    attempts += 1
    
    # Write new value back
    with open(attempts_file, "w") as f:
        f.write(str(attempts))
    
    print(f"Attempt {attempts}")
    
    # Decide success/failure
    if attempts < 3:
        raise Exception(f"Failing attempt {attempts}")
    
    return {
        "status": "success",
        "attempt": attempts
    }

def run_worker_process(worker_name):
    worker = hatchet.worker(worker_name, workflows=[flaky_task])
    worker.start()

def main():
    zealt_run_id = os.getenv("ZEALT_RUN_ID", "local")
    worker_name = f"task-retries-worker-{zealt_run_id}"
    
    # Ensure /tmp/attempts.txt does not exist before starting
    attempts_file = "/tmp/attempts.txt"
    if os.path.exists(attempts_file):
        os.remove(attempts_file)
    
    # Start worker in a separate process
    p = multiprocessing.Process(target=run_worker_process, args=(worker_name,))
    p.start()
    
    try:
        # Give worker some time to register
        time.sleep(5)
        
        # Trigger exactly one run of flaky_task
        print("Triggering task...")
        result = flaky_task.run({})
        
        # result might be a Pydantic model (EmptyModel) if it's empty, 
        # but here it should be the dict we returned.
        # If it's a Pydantic model, we should convert it to a dict.
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        elif hasattr(result, "dict"):
            result_dict = result.dict()
        else:
            result_dict = result

        # Write final task output to /tmp/result.json
        with open("/tmp/result.json", "w") as f:
            json.dump(result_dict, f)
        
        print(f"Task finished with result: {result_dict}")
        
    finally:
        # Shut down worker
        print("Shutting down worker...")
        p.terminate()
        p.join()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
