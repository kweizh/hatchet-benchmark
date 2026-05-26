import asyncio
import os
import sys
import time
import subprocess
from pydantic import BaseModel
from hatchet_sdk import Hatchet, ConcurrencyExpression, ConcurrencyLimitStrategy, Context

class PaymentInput(BaseModel):
    user_id: str

hatchet = Hatchet()

@hatchet.task(
    name="test_input",
    input_validator=PaymentInput,
)
def test_input_task(input: PaymentInput, context: Context):
    print("TYPE OF INPUT:", type(input))
    print("INPUT user_id:", input.user_id)
    return {"status": "done"}

def run_worker():
    worker = hatchet.worker("test_worker", slots=4)
    worker.register_workflow(test_input_task)
    worker.start()

async def trigger():
    ref = await test_input_task.aio_run(PaymentInput(user_id="A"), wait_for_result=False)
    await ref.aio_result()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        run_worker()
    else:
        proc = subprocess.Popen([sys.executable, "test_input.py", "worker"])
        time.sleep(2)
        asyncio.run(trigger())
        proc.terminate()
        proc.wait()
