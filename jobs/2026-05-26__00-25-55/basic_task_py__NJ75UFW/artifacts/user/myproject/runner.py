import os
import json
import threading
import time
from hatchet_sdk import Hatchet, Context

def run():
    zealt_run_id = os.getenv("ZEALT_RUN_ID")
    if not zealt_run_id:
        raise ValueError("ZEALT_RUN_ID environment variable is not set")

    hatchet = Hatchet()

    workflow = hatchet.workflow(name="simple_greeting", on_events=["simple:greeting"])

    @workflow.task()
    def simple_greeting(input, context: Context):
        # The input passed here seems to be an EmptyModel if not typed.
        # But wait, the previous error was 'EmptyModel' object has no attribute 'get'.
        # Let's try to see what 'input' actually is by printing it to stdout (which goes to log).
        print(f"DEBUG: input type is {type(input)}, value is {input}")
        
        # If it's a Pydantic model, we might need to use .model_dump() or access attributes.
        # But the requirement says input is a JSON object {"name": str}.
        
        try:
            name = input.name
        except AttributeError:
            try:
                name = input.get("name")
            except AttributeError:
                # Fallback to context
                workflow_input = context.workflow_input()
                name = workflow_input.get("name")
                
        return {"greeting": f"Hello, {name}!"}

    worker_name = f"basic-task-worker-{zealt_run_id}"
    worker = hatchet.worker(worker_name)
    worker.register_workflow(workflow)

    # Start worker in a separate thread
    worker_thread = threading.Thread(target=worker.start)
    worker_thread.daemon = True
    worker_thread.start()

    # Give the worker a moment to register/start
    time.sleep(10)

    try:
        # Trigger the workflow
        print("Triggering workflow...")
        # Increase timeout or just wait
        result = workflow.run(input={"name": "World"})
        
        print(f"Result received: {result}")

        # Write result to /tmp/result.json
        with open("/tmp/result.json", "w") as f:
            json.dump(result, f)
            
        print("Result written to /tmp/result.json")

    finally:
        # Shutdown worker
        print("Shutting down worker...")
        # Give it a tiny bit of time to cleanup if needed
        time.sleep(1)

if __name__ == "__main__":
    run()
