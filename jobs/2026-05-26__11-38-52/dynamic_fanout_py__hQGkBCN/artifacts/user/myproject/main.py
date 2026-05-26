import os
import json
import time
import multiprocessing
from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel
from typing import List

class SquareInput(BaseModel):
    item: int

class ProcessBatchInput(BaseModel):
    items: List[int]

hatchet = Hatchet()

@hatchet.task(name='square_item', input_validator=SquareInput)
def square_item(input: SquareInput, context: Context) -> dict:
    item = input.item
    return {"square": item * item}

@hatchet.task(name='process_batch', input_validator=ProcessBatchInput)
def process_batch(input: ProcessBatchInput, context: Context) -> dict:
    items = input.items
    
    # Create bulk run items
    # Create input objects using the expected model
    bulk_items = [square_item.create_bulk_run_item(input=SquareInput(item=i)) for i in items]
    
    # Run the children
    results = square_item.run_many(bulk_items)
    
    # Extract squares
    squares = [res["square"] for res in results]
    
    return {"squares": squares}

def run_worker():
    worker = hatchet.worker('my-worker')
    worker.register_workflow(square_item)
    worker.register_workflow(process_batch)
    worker.start()

if __name__ == "__main__":
    p = multiprocessing.Process(target=run_worker)
    p.start()
    
    try:
        # Give worker time to connect
        time.sleep(5)
        
        print("Triggering process_batch...")
        run_result = process_batch.run(input=ProcessBatchInput(items=[1, 2, 3, 4, 5]))
        
        print("Result:", run_result)
        
        with open("/tmp/result.json", "w") as f:
            json.dump(run_result, f)
            
        print("Wrote result to /tmp/result.json")
    finally:
        p.terminate()
        p.join()
