"""
Priority-based reordering demonstration using Hatchet Python SDK.

Enqueues 5 runs of a single-slot worker task (3 at priority 1, then 2 at
priority 3) and waits for all to complete.  Because the worker has only one
execution slot, queued runs are served in priority order, so the two
priority-3 runs overtake the remaining priority-1 runs.
"""

import os
import sys
import time
import threading

from hatchet_sdk import Context, Hatchet

# ── runtime configuration ──────────────────────────────────────────────────

RUN_ID = os.environ.get("ZEALT_RUN_ID", "default")
TASK_NAME = f"prio-task-{RUN_ID}"
LOG_FILE = f"/tmp/prio_log_{RUN_ID}.txt"

# ── Hatchet client (must be created at module load) ────────────────────────

hatchet = Hatchet()

# ── task definition ────────────────────────────────────────────────────────

@hatchet.task(name=TASK_NAME, default_priority=1, execution_timeout=__import__('datetime').timedelta(seconds=30))
def prio_task(input, ctx: Context):
    """Single task body: log priority + epoch_ms, then sleep 2 s."""
    # Read effective priority from the run context
    priority = ctx.priority if ctx.priority is not None else 1

    # Current epoch time in milliseconds
    epoch_ms = int(time.time() * 1000)

    # Append one line to the shared log file
    with open(LOG_FILE, "a") as fh:
        fh.write(f"{priority} {epoch_ms}\n")

    # Simulate ~2 seconds of work
    time.sleep(2)

    return {"priority": priority, "epoch_ms": epoch_ms}


# ── worker + runner ────────────────────────────────────────────────────────

def run():
    # 1. Truncate (create fresh) the log file.
    with open(LOG_FILE, "w") as fh:
        pass

    # 2. Build a single-slot worker.
    worker = hatchet.worker(
        name=f"prio-worker-{RUN_ID}",
        slots=1,
        workflows=[prio_task],
    )

    # 3. Start the worker in a background thread.
    #    worker.start() runs the asyncio event loop forever, so we need a
    #    daemon thread so that the main thread can continue to submit runs.
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()

    # Give the worker a moment to connect and register.
    time.sleep(5)

    # 4. Submit 5 runs with no waiting between submissions.
    #    First 3 at priority 1 (low), then 2 at priority 3 (high).
    refs = []

    for _ in range(3):
        ref = prio_task.run(wait_for_result=False, priority=1)
        refs.append(ref)

    for _ in range(2):
        ref = prio_task.run(wait_for_result=False, priority=3)
        refs.append(ref)

    print(f"Submitted 5 runs. Waiting for completion…", flush=True)

    # 5. Wait for all 5 runs to complete (blocks until each result arrives).
    for i, ref in enumerate(refs):
        try:
            result = ref.result()
            print(f"  run {i+1} done: {result}", flush=True)
        except Exception as exc:
            print(f"  run {i+1} error: {exc}", flush=True)

    print("All runs complete.", flush=True)

    # 6. Stop the worker cleanly.
    #    Signal the worker's event loop to exit gracefully, then join the
    #    thread.  We schedule exit_gracefully() on the worker's own loop.
    import asyncio, contextlib

    loop = worker._loop
    if loop is not None and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(worker.exit_gracefully(), loop)
        with contextlib.suppress(Exception):
            future.result(timeout=10)
        # Stop the loop so worker_thread finishes
        loop.call_soon_threadsafe(loop.stop)

    worker_thread.join(timeout=15)
    print("Worker stopped. Exiting.", flush=True)


if __name__ == "__main__":
    run()
