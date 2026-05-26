import os
import json
import asyncio
import multiprocessing
from hatchet_sdk import Hatchet

# Read ZEALT_RUN_ID from environment
zealt_run_id = os.getenv("ZEALT_RUN_ID", "default")
workflow_name = f"linear-dag-{zealt_run_id}"

# Initialize Hatchet client
hatchet = Hatchet()

# Using the functional API for workflows in v1
workflow = hatchet.workflow(name=workflow_name)

@workflow.task()
def step1_load(input, ctx):
    return {"text": "hello"}

@workflow.task(parents=[step1_load])
def step2_transform(input, ctx):
    # Read parent output via the task object
    parent_output = ctx.task_output(step1_load)
    # If it's a Pydantic model, use dot notation or access via __dict__
    if hasattr(parent_output, "text"):
        text = parent_output.text
    elif isinstance(parent_output, dict):
        text = parent_output.get("text")
    else:
        # Try to access as dict-like if it's a model
        try:
            text = parent_output["text"]
        except:
            text = getattr(parent_output, "text", None)
            
    return {"text": f"{text} world"}

@workflow.task(parents=[step2_transform])
def step3_finalize(input, ctx):
    # Read parent output
    parent_output = ctx.task_output(step2_transform)
    if hasattr(parent_output, "text"):
        text = parent_output.text
    elif isinstance(parent_output, dict):
        text = parent_output.get("text")
    else:
        try:
            text = parent_output["text"]
        except:
            text = getattr(parent_output, "text", None)
            
    return {"final": f"{text}!"}

def run_worker():
    # New process, new loop
    worker = hatchet.worker("linear-dag-worker")
    worker.register_workflow(workflow)
    worker.start()

async def trigger_and_wait():
    print(f"Triggering workflow: {workflow_name}")
    try:
        # Give worker time to start in the other process
        await asyncio.sleep(5)
        
        # Trigger the workflow and wait for the result
        result = await workflow.aio_run()
        print(f"Workflow completed with result: {result}")
        
        final_output = None
        if isinstance(result, dict):
            # The keys are the task names
            if "step3_finalize" in result:
                final_output = result["step3_finalize"]
                # If it's a model, convert to dict
                if hasattr(final_output, "model_dump"):
                    final_output = final_output.model_dump()
                elif hasattr(final_output, "__dict__"):
                    # Basic check for dict-like
                    if not isinstance(final_output, dict):
                         final_output = {"final": getattr(final_output, "final", None)}
            elif "final" in result:
                final_output = result
            else:
                # Fallback: check if any value is the final result
                for v in result.values():
                    if hasattr(v, "final") or (isinstance(v, dict) and "final" in v):
                        if hasattr(v, "model_dump"):
                            final_output = v.model_dump()
                        else:
                            final_output = v
                        break
                if not final_output:
                    final_output = result
        
        if final_output:
            # Final sanity check: make sure it's a dict for JSON dump
            if not isinstance(final_output, dict):
                if hasattr(final_output, "model_dump"):
                    final_output = final_output.model_dump()
                elif hasattr(final_output, "__dict__"):
                    final_output = dict(final_output)

            with open("/tmp/result.json", "w") as f:
                json.dump(final_output, f)
            print("Result saved to /tmp/result.json")
        else:
            print("Could not find final output")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Start worker in a separate process
    p = multiprocessing.Process(target=run_worker)
    p.start()
    
    try:
        # Run the trigger in the main process
        asyncio.run(trigger_and_wait())
    finally:
        # Kill the worker process
        p.terminate()
        p.join()
