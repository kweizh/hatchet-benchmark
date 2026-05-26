"""
Hatchet worker definition for the process_payment task.

This module defines the task with per-user-id concurrency control
(max_runs=1 per user_id key, GROUP_ROUND_ROBIN strategy) and starts
a worker when run directly.
"""

import os
import time

from pydantic import BaseModel

from hatchet_sdk import ConcurrencyExpression, ConcurrencyLimitStrategy, Hatchet

# Read the run-id from environment so task names are unique per grader trial.
RUN_ID = os.environ.get("ZEALT_RUN_ID", "local")
TASK_NAME = f"process-payment-{RUN_ID}"
WORKER_NAME = f"payment-worker-{RUN_ID}"
LOG_PATH = "/tmp/runs.log"

hatchet = Hatchet()


class PaymentInput(BaseModel):
    user_id: str


@hatchet.task(
    name=TASK_NAME,
    input_validator=PaymentInput,
    # Serialize at most 1 run per user_id; queue extras with fair round-robin.
    concurrency=ConcurrencyExpression(
        expression="input.user_id",
        max_runs=1,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
    # Give each run enough time: 2 s work + scheduling headroom.
    execution_timeout="120s",
    schedule_timeout="120s",
)
def process_payment(input: PaymentInput, ctx) -> dict:
    with open(LOG_PATH, "a") as f:
        f.write(f"start {input.user_id} {time.time()}\n")
        f.flush()

    time.sleep(2)

    with open(LOG_PATH, "a") as f:
        f.write(f"end {input.user_id} {time.time()}\n")
        f.flush()

    return {"user_id": input.user_id}


def main() -> None:
    # Worker needs >= 4 slots so it is never the bottleneck.
    worker = hatchet.worker(
        WORKER_NAME,
        slots=10,
        workflows=[process_payment],
    )
    worker.start()


if __name__ == "__main__":
    main()
