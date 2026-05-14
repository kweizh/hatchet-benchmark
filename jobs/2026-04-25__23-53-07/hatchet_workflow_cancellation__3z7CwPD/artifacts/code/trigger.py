#!/usr/bin/env python3
import time
import os
from hatchet_sdk import Hatchet

hatchet = Hatchet()

def main():
    # Trigger the workflow run asynchronously
    workflow_run_id = hatchet.admin.run_workflow("cancellation_workflow", {})
    
    # Write the workflow_run_id to run_id.txt in the project directory
    run_id_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_id.txt")
    with open(run_id_path, "w") as f:
        f.write(workflow_run_id)
    
    print(f"Triggered workflow run: {workflow_run_id}")
    
    # Sleep for 2 seconds
    time.sleep(2)
    
    # Cancel the workflow run using hatchet.runs.cancel
    hatchet.runs.cancel(workflow_run_id)
    print(f"Cancelled workflow run: {workflow_run_id}")

if __name__ == "__main__":
    main()
