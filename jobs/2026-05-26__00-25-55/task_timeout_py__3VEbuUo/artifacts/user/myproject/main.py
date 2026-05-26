import os
import time
import json
import asyncio
import threading
from hatchet_sdk import Hatchet
from dotenv import load_dotenv

load_dotenv()

# Get run ID for task isolation
run_id = os.getenv("ZEALT_RUN_ID", "default-run-id")
task_name = f"slow_task_{run_id}"

hatchet = Hatchet()

@hatchet.task(
    name=task_name,
    execution_timeout="5s",
    retries=0
)
async def slow_task(input, context):
    print(f"Starting {task_name}, will sleep for 20s...")
    await asyncio.sleep(20)
    return {"status": "completed"}

def run_worker(worker):
    print("Worker thread starting...")
    worker.start()
    print("Worker thread exiting...")

async def main():
    worker = hatchet.worker(f"worker-{run_id}")
    worker.register_workflow(slow_task._workflow)
    
    # Start worker in a separate thread because .start() is blocking
    worker_thread = threading.Thread(target=run_worker, args=(worker,), daemon=True)
    worker_thread.start()
    
    # Wait a bit for worker to be ready
    await asyncio.sleep(5)
    
    result_data = {}
    try:
        print(f"Triggering {task_name}...")
        # Trigger and wait for result
        workflow_run = await slow_task.aio_run({})
        
        # We use a loop to check the result to avoid blocking issues
        # and ensure we catch the timeout.
        start_wait = time.time()
        while time.time() - start_wait < 40:
            try:
                # To be safe, let's use the admin client directly to poll
                details = hatchet.client.admin.get_details(workflow_run.workflow_run_id)
                from hatchet_sdk.clients.admin import RunStatus
                
                print(f"Current status: {details.status}")
                
                if details.status == RunStatus.COMPLETED:
                    print("Task unexpectedly succeeded")
                    result_data = {"timed_out": False}
                    break
                elif details.status == RunStatus.FAILED:
                    print("Task failed as expected")
                    # Collect errors
                    errors = [run.error for run in details.task_runs.values() if run.error]
                    result_data = {"timed_out": True, "error": str(errors)}
                    break
                elif details.status == RunStatus.CANCELLED:
                    print("Task was cancelled (this usually happens on timeout)")
                    result_data = {"timed_out": True, "error": "Task was cancelled"}
                    break
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(2)
        else:
            print("Runner script timed out waiting for Hatchet")
            result_data = {"timed_out": True, "error": "Runner script timeout"}
            
    except Exception as e:
        print(f"Caught trigger exception: {e}")
        result_data = {"timed_out": True, "error": str(e)}
    finally:
        # We can't easily stop the worker from here if it's in run_forever()
        # but the thread is daemon, so it will exit when main exits.
        # However, we should try to be clean if possible.
        # Worker doesn't have a simple stop() that works across threads easily without signals.
        
        # Write result to /tmp/result.json
        with open("/tmp/result.json", "w") as f:
            json.dump(result_data, f)
        print("Result written to /tmp/result.json")

if __name__ == "__main__":
    asyncio.run(main())
    # Force exit to kill the daemon worker thread
    os._exit(0)
