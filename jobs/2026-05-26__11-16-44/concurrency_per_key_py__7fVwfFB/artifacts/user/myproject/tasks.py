import os
import time
from pydantic import BaseModel
from hatchet_sdk import Hatchet, ConcurrencyExpression, ConcurrencyLimitStrategy, Context

LOG_PATH = "/tmp/runs.log"
RUN_ID = os.environ.get("ZEALT_RUN_ID", "local")
TASK_NAME = f"process-payment-{RUN_ID}"
WORKER_NAME = f"process-payment-worker-{RUN_ID}"

hatchet = Hatchet()


class PaymentInput(BaseModel):
    user_id: str


def _append_log(event: str, user_id: str) -> None:
    timestamp = time.time()
    line = f"{event} {user_id} {timestamp}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


@hatchet.task(
    name=TASK_NAME,
    input_validator=PaymentInput,
    concurrency=ConcurrencyExpression(
        expression="input.user_id",
        max_runs=1,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
def process_payment(input: PaymentInput, ctx: Context) -> None:
    _append_log("start", input.user_id)
    time.sleep(2)
    _append_log("end", input.user_id)
