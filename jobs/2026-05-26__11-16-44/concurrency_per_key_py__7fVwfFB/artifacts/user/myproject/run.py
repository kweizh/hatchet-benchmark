import asyncio
import os
import subprocess
import sys
import time

from tasks import PaymentInput, process_payment

LOG_PATH = "/tmp/runs.log"


def _start_worker() -> subprocess.Popen:
    worker_path = os.path.join(os.path.dirname(__file__), "worker.py")
    return subprocess.Popen([sys.executable, worker_path], env=os.environ.copy())


async def _trigger_runs() -> None:
    items = [
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="A")),
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="A")),
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="B")),
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="B")),
    ]
    await process_payment.aio_run_many(items)


def main() -> None:
    with open(LOG_PATH, "w", encoding="utf-8"):
        pass

    worker_process = _start_worker()
    try:
        time.sleep(2)
        asyncio.run(_trigger_runs())
    finally:
        worker_process.terminate()
        try:
            worker_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker_process.kill()
            worker_process.wait(timeout=5)


if __name__ == "__main__":
    main()
