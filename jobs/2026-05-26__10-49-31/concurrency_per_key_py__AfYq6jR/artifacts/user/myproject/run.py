"""
Runner: starts the Hatchet worker in a background subprocess, triggers
four concurrent process_payment runs (2 for user A, 2 for user B),
waits for all four to finish, then terminates the worker.

Produces /tmp/runs.log with exactly 8 lines that prove per-key
serialization (no overlap within same user_id, overlap allowed across
different user_ids).
"""

import asyncio
import os
import sys
import subprocess
import time

# ---------------------------------------------------------------------------
# Import shared constants from worker module (task name, input model).
# ---------------------------------------------------------------------------
from worker import TASK_NAME, PaymentInput, process_payment

LOG_PATH = "/tmp/runs.log"

# Clear any previous log so the verifier sees exactly 8 lines.
open(LOG_PATH, "w").close()


async def main() -> None:
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # ------------------------------------------------------------------
    # 1. Start the worker in a background subprocess.
    # ------------------------------------------------------------------
    worker_proc = subprocess.Popen(
        [sys.executable, "worker.py"],
        cwd=project_dir,
        env=os.environ.copy(),
    )

    # Give the worker time to register itself with Hatchet Cloud before
    # we push any runs.
    print("[run.py] Waiting for worker to register…", flush=True)
    await asyncio.sleep(8)

    # ------------------------------------------------------------------
    # 2. Trigger 4 runs concurrently via aio_run_many.
    # ------------------------------------------------------------------
    print(f"[run.py] Triggering 4 runs for task '{TASK_NAME}'…", flush=True)

    configs = [
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="A")),
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="A")),
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="B")),
        process_payment.create_bulk_run_item(input=PaymentInput(user_id="B")),
    ]

    # aio_run_many with wait_for_result=True blocks until every run has
    # finished (or raises on failure).
    results = await process_payment.aio_run_many(
        configs,
        return_exceptions=True,
        wait_for_result=True,
    )

    print(f"[run.py] All runs finished. Results: {results}", flush=True)

    # ------------------------------------------------------------------
    # 3. Verify the log has exactly 8 lines before we exit.
    # ------------------------------------------------------------------
    try:
        with open(LOG_PATH) as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"[run.py] Log lines ({len(lines)}):")
        for line in lines:
            print(f"  {line}")
        assert len(lines) == 8, f"Expected 8 log lines, got {len(lines)}"
    except Exception as exc:
        print(f"[run.py] Log check failed: {exc}", flush=True)
        raise
    finally:
        # ------------------------------------------------------------------
        # 4. Terminate the worker process cleanly.
        # ------------------------------------------------------------------
        print("[run.py] Terminating worker…", flush=True)
        worker_proc.terminate()
        try:
            worker_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
            worker_proc.wait()

    print("[run.py] Done.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
