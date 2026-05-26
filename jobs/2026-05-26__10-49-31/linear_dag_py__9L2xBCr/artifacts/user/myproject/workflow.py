"""
Linear DAG workflow with three sequential tasks on Hatchet Cloud.

This script:
1. Defines a 3-task linear DAG workflow
2. Starts the worker in a background subprocess
3. Triggers the workflow and waits for the result
4. Writes the final output to /tmp/result.json
"""
import json
import os
import subprocess
import sys
import time

from hatchet_sdk import Context, Hatchet

# Build unique workflow name from ZEALT_RUN_ID
run_id = os.environ["ZEALT_RUN_ID"]
workflow_name = f"linear-dag-{run_id}"

hatchet = Hatchet()

# Declare the workflow
wf = hatchet.workflow(name=workflow_name)


@wf.task()
def step1_load(input, ctx: Context):
    return {"text": "hello"}


@wf.task(parents=[step1_load])
def step2_transform(input, ctx: Context):
    parent_output = ctx.task_output(step1_load)
    text = parent_output["text"]
    return {"text": f"{text} world"}


@wf.task(parents=[step2_transform])
def step3_finalize(input, ctx: Context):
    parent_output = ctx.task_output(step2_transform)
    text = parent_output["text"]
    return {"final": f"{text}!"}


if __name__ == "__main__":
    worker_script = os.path.join(os.path.dirname(__file__), "worker_process.py")

    # Start the worker subprocess in the background
    worker_proc = subprocess.Popen(
        [sys.executable, worker_script],
        env=os.environ.copy(),
    )
    print(f"Worker process started with PID {worker_proc.pid}")

    try:
        # Give the worker time to connect and register with Hatchet Cloud
        time.sleep(8)

        # Trigger the workflow and wait for the result
        result = wf.run()
        print(f"Full result from wf.run(): {result}")

        # Extract the step3_finalize output
        # result is a dict keyed by task readable_id (function name) -> task output dict
        final_output = result.get("step3_finalize")
        if final_output is None:
            # Fallback: search for a key containing "step3_finalize"
            for key, val in result.items():
                if "step3_finalize" in key:
                    final_output = val
                    break

        if final_output is None:
            raise RuntimeError(
                f"step3_finalize output not found in result: {result}"
            )

        print(f"step3_finalize output: {final_output}")

        # Write result to /tmp/result.json
        with open("/tmp/result.json", "w") as f:
            json.dump(final_output, f)

        print(f"Result written to /tmp/result.json: {final_output}")
    finally:
        worker_proc.terminate()
        worker_proc.wait(timeout=10)
        print("Worker process terminated.")
