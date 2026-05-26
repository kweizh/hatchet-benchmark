import os
import json
import threading
import time
from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class GreetingInput(BaseModel):
    name: str

class GreetingOutput(BaseModel):
    greeting: str

@hatchet.task()
def simple_greeting(input_data: GreetingInput, context: Context) -> GreetingOutput:
    return GreetingOutput(greeting=f"Hello, {input_data.name}!")

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
    print("Result dict:", result.model_dump())
    
    # write result to /tmp/result.json
    with open("/tmp/result.json", "w") as f:
        json.dump(result.model_dump(), f)

if __name__ == "__main__":
    main()
