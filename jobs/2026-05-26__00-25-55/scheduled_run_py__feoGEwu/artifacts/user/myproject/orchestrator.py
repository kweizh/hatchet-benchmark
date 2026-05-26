import json
import os
import time
from datetime import datetime, timedelta, timezone
import multiprocessing
from hatchet_sdk import Hatchet

# Initialize Hatchet client
hatchet = Hatchet()

# Define the Hatchet task
@hatchet.task(name="scheduled-hello")
def scheduled_hello(workflow_input, context):
    # Convert Pydantic model to dict if necessary
    input_data = workflow_input
    if hasattr(workflow_input, 'model_dump'):
        input_data = workflow_input.model_dump()
    elif hasattr(workflow_input, 'dict'):
        input_data = workflow_input.dict()
    elif not isinstance(workflow_input, dict):
        try:
            input_data = dict(workflow_input)
        except:
            input_data = str(workflow_input)

    print(f"Task 'scheduled-hello' fired with input: {input_data}")
    
    # Prepare the result object
    result = {
        "fired_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input": input_data
    }
    
    # Write the result to the specified file
    result_path = "/tmp/scheduled_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f)
    
    print(f"Result written to {result_path}")
    return result

def run_worker():
    # Create and start a worker that handles the 'scheduled-hello' task
    # We need a new Hatchet instance in the sub-process
    worker_hatchet = Hatchet()
    worker = worker_hatchet.worker("scheduled-worker")
    worker.register_workflow(scheduled_hello)
    print("Worker starting to listen for tasks...")
    worker.start()

def main():
    # 1. Start a Hatchet worker in a background process
    print("Starting worker in background process...")
    worker_process = multiprocessing.Process(target=run_worker)
    worker_process.start()
    
    # Give the worker enough time to connect and register the task with Hatchet Cloud
    print("Waiting 15 seconds for worker to register task...")
    time.sleep(15)

    # 2. Programmatically schedule the task to run ONE TIME at now + 15 seconds
    run_at = datetime.now(timezone.utc) + timedelta(seconds=15)
    print(f"Scheduling task 'scheduled-hello' to run at {run_at} (UTC)")
    
    try:
        # Using the task object's schedule method
        schedule = scheduled_hello.schedule(
            run_at=run_at,
            input={"name": "world"}
        )
        
        print(f"Schedule return type: {type(schedule)}")
        print(f"Schedule return value: {schedule}")
        
        # Try to get the ID.
        if hasattr(schedule, 'scheduled_workflows') and len(schedule.scheduled_workflows) > 0:
            scheduled_id = schedule.scheduled_workflows[0].id
        elif isinstance(schedule, dict) and 'scheduled_workflows' in schedule:
            scheduled_id = schedule['scheduled_workflows'][0]['id']
        else:
            # Fallback
            try:
                scheduled_id = schedule.metadata.id
            except:
                scheduled_id = str(schedule)
        
        print(f"Successfully scheduled task. Scheduled ID: {scheduled_id}")
        
        # 3. Wait for the scheduled time to pass and for the task to execute
        # We wait 45 seconds total (15s for the schedule + 30s buffer)
        wait_time = 45
        print(f"Waiting {wait_time} seconds for task execution...")
        time.sleep(wait_time)
        
        # 4. Verify the task execution result
        result_path = "/tmp/scheduled_result.json"
        if os.path.exists(result_path):
            print("Verification: /tmp/scheduled_result.json found.")
            try:
                with open(result_path, "r") as f:
                    content = json.load(f)
                    print(f"File content: {json.dumps(content, indent=2)}")
            except Exception as e:
                print(f"Error reading/parsing result file: {e}")
                # Print file content for debugging
                with open(result_path, "r") as f:
                    print(f"Raw file content: {f.read()}")
        else:
            print("Verification FAILED: /tmp/scheduled_result.json not found.")
        
        # 5. Clean up the scheduled run via the SDK
        print(f"Cleaning up: Deleting scheduled run {scheduled_id}...")
        try:
            hatchet.scheduled.delete(scheduled_id=scheduled_id)
            print("Schedule deleted successfully.")
        except Exception as e:
            print(f"Error deleting schedule: {e}")
            
    except Exception as e:
        print(f"Error during scheduling/execution: {e}")
    finally:
        # Terminate the worker process
        print("Terminating worker process...")
        worker_process.terminate()
        worker_process.join()

    print("Orchestration finished.")

if __name__ == "__main__":
    main()
