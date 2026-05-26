import os
import time
from hatchet_sdk import Hatchet, ConcurrencyExpression, ConcurrencyLimitStrategy
from pydantic import BaseModel

run_id = os.getenv("ZEALT_RUN_ID", "default")
task_name = f"process-payment-{run_id}"

hatchet = Hatchet()

class PaymentInput(BaseModel):
    user_id: str

@hatchet.task(
    name=task_name,
    input_validator=PaymentInput,
    concurrency=ConcurrencyExpression(
        expression="input.user_id",
        max_runs=1,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN
    )
)
def process_payment(input_data: PaymentInput, context):
    # The input_data is already validated and passed as the first argument
    user_id = input_data.user_id
    
    log_path = "/tmp/runs.log"
    
    # Start log
    with open(log_path, "a") as f:
        f.write(f"start {user_id} {time.time()}\n")
        f.flush()
    
    # Simulate work
    time.sleep(2)
    
    # End log
    with open(log_path, "a") as f:
        f.write(f"end {user_id} {time.time()}\n")
        f.flush()

if __name__ == "__main__":
    # worker slots >= 4
    worker = hatchet.worker(f"worker-{run_id}", slots=10)
    worker.register_workflow(process_payment)
    worker.start()
