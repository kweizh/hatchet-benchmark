import os
import json
import threading
import time
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

@hatchet.task()
def simple_greeting(context: Context):
    input_data = context.workflow_input()
    name = input_data.get("name", "")
    return {"greeting": f"Hello, {name}!"}

def main():
    worker_name = "test-worker"
    worker = hatchet.worker(worker_name)
    worker.register_workflow(simple_greeting)
    
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    time.sleep(2)
    
    print("Running task")
    result = simple_greeting.run({"name": "World"})
    print("Result:", result)
    
    # how to stop worker?
    # worker.exit_gracefully() ? wait, let's check worker methods
    # we saw exit_gracefully in the dir(worker)

if __name__ == "__main__":
    main()
