import json
import threading
import time

from hatchet_sdk import Context, Hatchet

hatchet = Hatchet()

workflow = hatchet.workflow(name="diamond-dag")


@workflow.task()
def start(input, ctx: Context) -> dict:
    return {"value": 10}


@workflow.task(parents=[start])
def branch_a(input, ctx: Context) -> dict:
    start_output = ctx.task_output(start)
    return {"a": start_output["value"] * 2}


@workflow.task(parents=[start])
def branch_b(input, ctx: Context) -> dict:
    start_output = ctx.task_output(start)
    return {"b": start_output["value"] + 5}


@workflow.task(parents=[branch_a, branch_b])
def merge(input, ctx: Context) -> dict:
    a_output = ctx.task_output(branch_a)
    b_output = ctx.task_output(branch_b)
    return {"sum": a_output["a"] + b_output["b"]}


def run_worker():
    worker = hatchet.worker("diamond-worker", workflows=[workflow])
    worker.start()


if __name__ == "__main__":
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()

    # Give the worker a moment to connect and register
    time.sleep(3)

    print("Triggering workflow run...")
    result = workflow.run()

    print(f"Workflow completed. Result: {result}")

    merge_output = result.get("merge", result)

    with open("/tmp/result.json", "w") as f:
        json.dump(merge_output, f, indent=2)

    print(f"Result written to /tmp/result.json: {merge_output}")
