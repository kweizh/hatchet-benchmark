import json
from hatchet_sdk import Hatchet, Context

# Initialize Hatchet client
hatchet = Hatchet()

# Define the workflow
workflow = hatchet.workflow(
    name="EventWorkflow",
    on_events=["user:create"]
)

@workflow.task()
def process_event(input: dict, context: Context):
    # The 'input' parameter contains the event payload
    
    # Define output path
    output_path = "/home/user/hatchet-worker/output.json"
    
    # Write payload to output.json
    with open(output_path, "w") as f:
        json.dump(input, f, indent=4)
    
    print(f"Processed event and wrote to {output_path}")
    return {"status": "success", "file": output_path}

def main():
    # Create a worker named 'event-worker'
    worker = hatchet.worker("event-worker")
    
    # Register the workflow
    worker.register_workflow(workflow)
    
    print("Starting worker 'event-worker'...")
    # Start the worker (keep running)
    worker.start()

if __name__ == "__main__":
    main()
