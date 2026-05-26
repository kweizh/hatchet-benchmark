import os
import json
import time
import subprocess
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()
run_id = os.environ.get("ZEALT_RUN_ID", "test-run")
workflow_name = f"linear-dag-{run_id}"

workflow = hatchet.workflow(name=workflow_name)

@workflow.task()
def step1_load(input, ctx: Context) -> dict:
    return {"text": "hello"}

@workflow.task(parents=[step1_load])
def step2_transform(input, ctx: Context) -> dict:
    step1_text = ctx.task_output(step1_load)["text"]
    return {"text": f"{step1_text} world"}

@workflow.task(parents=[step2_transform])
def step3_finalize(input, ctx: Context) -> dict:
    step2_text = ctx.task_output(step2_transform)["text"]
    return {"final": f"{step2_text}!"}

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        # Run worker
        worker = hatchet.worker("linear-dag-worker", slots=10)
        worker.register_workflow(workflow)
        worker.start()
        return

    # Start the worker as a subprocess
    worker_proc = subprocess.Popen([sys.executable, __file__, "worker"])
    
    try:
        # Wait a bit for the worker to start
        time.sleep(3)
        
        # Trigger the workflow
        print("Triggering workflow...")
        result = workflow.run()
        print("Workflow result:", result)
        
        final_output = result.get("step3_finalize", {})
        
        # Save to /tmp/result.json
        with open('/tmp/result.json', 'w') as f:
            json.dump(final_output, f)
            
    finally:
        # Terminate the worker
        worker_proc.terminate()
        worker_proc.wait()

if __name__ == "__main__":
    main()
