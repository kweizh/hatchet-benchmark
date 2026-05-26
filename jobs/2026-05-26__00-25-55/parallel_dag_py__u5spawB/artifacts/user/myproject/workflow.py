import json
import time
import multiprocessing
import os
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

# Define the workflow
workflow = hatchet.workflow(name="DiamondWorkflow", on_events=["diamond:create"])

@workflow.task()
def start(workflow_input, ctx: Context):
    return {"value": 10}

@workflow.task(parents=[start])
def branch_a(workflow_input, ctx: Context):
    output = ctx.task_output(start)
    if hasattr(output, 'value'):
        start_val = output.value
    elif isinstance(output, dict):
        start_val = output["value"]
    else:
        try:
            start_val = output.model_dump()["value"]
        except:
            start_val = getattr(output, "value", 10)
            
    return {"a": start_val * 2}

@workflow.task(parents=[start])
def branch_b(workflow_input, ctx: Context):
    output = ctx.task_output(start)
    if hasattr(output, 'value'):
        start_val = output.value
    elif isinstance(output, dict):
        start_val = output["value"]
    else:
        try:
            start_val = output.model_dump()["value"]
        except:
            start_val = getattr(output, "value", 10)
            
    return {"b": start_val + 5}

@workflow.task(parents=[branch_a, branch_b])
def merge(workflow_input, ctx: Context):
    out_a = ctx.task_output(branch_a)
    out_b = ctx.task_output(branch_b)
    
    if hasattr(out_a, 'a'):
        a_val = out_a.a
    else:
        a_val = out_a.get("a") if isinstance(out_a, dict) else getattr(out_a, "a", 20)
        
    if hasattr(out_b, 'b'):
        b_val = out_b.b
    else:
        b_val = out_b.get("b") if isinstance(out_b, dict) else getattr(out_b, "b", 15)
        
    return {"sum": a_val + b_val}

def run_worker():
    worker = hatchet.worker("diamond-worker")
    worker.register_workflow(workflow)
    worker.start()

if __name__ == "__main__":
    worker_process = multiprocessing.Process(target=run_worker)
    worker_process.start()

    time.sleep(10)

    try:
        print("Triggering workflow...")
        # In this SDK version, workflow.run() seems to return the result directly if it blocks.
        result_data = workflow.run({})
        
        print(f"Workflow completed. Result: {result_data}")
        
        final_json = result_data
        # If it's a Pydantic model, convert to dict
        if hasattr(final_json, "model_dump"):
            final_json = final_json.model_dump()
        
        # If it's a dict containing all task outputs, extract 'merge'
        if isinstance(final_json, dict) and "merge" in final_json:
             final_json = final_json["merge"]

        with open("/tmp/result.json", "w") as f:
            json.dump(final_json, f)
        print("Result written to /tmp/result.json")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        worker_process.terminate()
        worker_process.join()
