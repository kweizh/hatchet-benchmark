import json
import time
import threading
from datetime import timedelta
from hatchet_sdk import Hatchet, DurableContext

# Initialize Hatchet
hatchet = Hatchet()

@hatchet.durable_task(name="delayed_greeting")
async def delayed_greeting(ctx: DurableContext):
    start_time = time.time()
    print(f"Task started at {start_time}")
    
    # Durable sleep for 5 seconds
    await ctx.aio_sleep_for(timedelta(seconds=5))
    
    end_time = time.time()
    elapsed_sec = int(end_time - start_time)
    print(f"Task finished at {end_time}, elapsed: {elapsed_sec}")
    
    return {
        "message": "wakeup",
        "elapsed_sec": elapsed_sec
    }

def main():
    # Create a worker
    worker = hatchet.worker("greeting-worker")
    worker.register_workflow(delayed_greeting)
    
    # Start the worker in a background thread
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    # Wait for worker to start and register
    time.sleep(5)
    
    # Trigger the task
    print("Triggering task...")
    
    # Use the public 'admin' property if available, or '_client.admin'
    # The TypeError suggests the 'input' argument (second arg) might need to be a string or dict
    # Let's try passing an empty dict explicitly or a JSON string.
    
    try:
        # Some versions use hatchet.admin
        admin_client = hatchet.admin
    except AttributeError:
        admin_client = hatchet._client.admin
    
    # Try passing input as a JSON string if {} failed
    workflow_run = admin_client.run_workflow("delayed_greeting", json.dumps({}))
    
    print("Waiting for result...")
    result = workflow_run.result()
    
    print(f"Result received: {result}")
    
    # Write to /tmp/result.json
    with open("/tmp/result.json", "w") as f:
        json.dump(result, f)
    
    print("Result written to /tmp/result.json. Exiting.")

if __name__ == "__main__":
    main()
