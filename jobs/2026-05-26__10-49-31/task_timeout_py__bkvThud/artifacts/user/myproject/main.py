"""
Hatchet Task Execution Timeout Demo

This script demonstrates how Hatchet cancels a task that exceeds its
execution_timeout. A slow_task is registered with a 5-second timeout
but sleeps for 20 seconds, causing Hatchet Cloud to cancel it.

The result is written to /tmp/result.json.
"""

import json
import os
import threading
import time
from datetime import timedelta

from hatchet_sdk import Context, Hatchet
from hatchet_sdk.exceptions import FailedTaskRunExceptionGroup, TaskRunError

# ── configuration ──────────────────────────────────────────────────────────────

# Include the run-id in the workflow name so concurrent test runs don't
# collide on the Hatchet Cloud workflow registry.
RUN_ID = os.environ.get("ZEALT_RUN_ID", "local")
TASK_NAME = f"slow_task-{RUN_ID}"

# ── Hatchet client & task definition ──────────────────────────────────────────

hatchet = Hatchet()


@hatchet.task(
    name=TASK_NAME,
    execution_timeout=timedelta(seconds=5),
    retries=0,
)
def slow_task(input, ctx: Context):
    """Sleeps for 20 seconds, intentionally exceeding the 5-second timeout."""
    time.sleep(20)
    return {"status": "completed"}  # should never be reached


# ── worker helpers ─────────────────────────────────────────────────────────────


def _run_worker() -> None:
    """
    Run the Hatchet worker in its own thread.  The worker calls
    `worker.start()` which blocks internally (it creates its own event loop),
    so we run it in a daemon thread so the process can exit even if the worker
    has not cleanly stopped.
    """
    worker = hatchet.worker(
        name=f"timeout-demo-worker-{RUN_ID}",
        workflows=[slow_task],
    )
    # worker.start() creates its own asyncio event loop and blocks.
    worker.start()


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    result_path = "/tmp/result.json"

    # Start the worker in a background daemon thread so it can receive and
    # execute the task while the main thread waits for the result.
    worker_thread = threading.Thread(target=_run_worker, daemon=True, name="hatchet-worker")
    worker_thread.start()

    # Give the worker a moment to connect and register before we trigger the task.
    time.sleep(5)

    result: dict
    try:
        # Trigger the task synchronously; this blocks until Hatchet reports
        # success or failure (including timeout cancellation).
        slow_task.run()
        # If we somehow reach here without an exception the task succeeded.
        result = {"timed_out": False}
    except (TaskRunError, FailedTaskRunExceptionGroup, Exception) as exc:
        result = {"timed_out": True, "error": str(exc)}

    # Write the result file.
    with open(result_path, "w") as fh:
        json.dump(result, fh)

    print(f"Result written to {result_path}: {result}")
    # Exit cleanly regardless of task outcome.


if __name__ == "__main__":
    main()
