import os
import sys
import time
import asyncio
import subprocess
from pydantic import BaseModel
from hatchet_sdk import Hatchet, ConcurrencyExpression, ConcurrencyLimitStrategy, Context

run_id = os.environ.get("ZEALT_RUN_ID", "local")
task_name = f"process_payment_{run_id}"
worker_name = f"worker_{run_id}"

class PaymentInput(BaseModel):
    user_id: str

hatchet = Hatchet()

@hatchet.task(
    name=task_name,
    input_validator=PaymentInput,
    concurrency=ConcurrencyExpression(
        expression="input.user_id",
        max_runs=1,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN
    )
)
def process_payment(context: Context):
    user_id = context.workflow_input()["user_id"]
    with open("/tmp/runs.log", "a") as f:
        f.write(f"start {user_id} {time.time()}\n")
        f.flush()
    
    time.sleep(2)
    
    with open("/tmp/runs.log", "a") as f:
        f.write(f"end {user_id} {time.time()}\n")
        f.flush()
    return {"status": "done"}

def run_worker():
    worker = hatchet.worker(worker_name, max_runs=4)
    worker.register_workflow(process_payment)
    worker.start()

async def main():
    # Start worker in a subprocess so we can easily kill it
    proc = subprocess.Popen([sys.executable, "-c", """
import run
run.run_worker()
"""])
    
    time.sleep(3) # Wait for worker to connect
    
    # Trigger 4 runs
    print("Triggering runs...")
    
    # In hatchet sdk, we can use hatchet.admin.run_workflow or hatchet.client.admin.run_workflow
    # Let's check the exact API for triggering a task.
    # Usually it's hatchet.client.admin.run_workflow(task_name, {"user_id": "A"})
