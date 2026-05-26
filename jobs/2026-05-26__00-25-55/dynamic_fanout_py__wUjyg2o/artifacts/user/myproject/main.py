import os
import json
import asyncio
import threading
import time
from workflows import hatchet, process_batch, square_item

def run_worker():
    # Create a new hatchet instance for the worker to avoid sharing state if necessary
    # but using the same one is usually fine.
    worker = hatchet.worker("test-worker")
    worker.register_workflow(square_item)
    worker.register_workflow(process_batch)
    worker.start()

async def main():
    # Start worker in a separate thread
    print("Starting worker...")
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    
    # Give the worker a moment to start and register
    print("Waiting for worker to initialize...")
    await asyncio.sleep(10)
    
    # Trigger parent workflow
    print("Triggering parent workflow 'process_batch' with items [1, 2, 3, 4, 5]...")
    try:
        # aio_run triggers and waits for result
        result = await process_batch.aio_run(input={"items": [1, 2, 3, 4, 5]})
        
        print(f"Workflow completed. Result: {result}")
        
        # Write result to /tmp/result.json
        output_path = "/tmp/result.json"
        with open(output_path, "w") as f:
            json.dump(result, f)
        
        print(f"Final output written to {output_path}")
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        # Log more details if possible
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
