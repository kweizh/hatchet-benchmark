#!/usr/bin/env python3
"""
Hatchet Task Retries with Exponential Backoff runner script.

This script:
1. Reads ZEALT_RUN_ID from the environment.
2. Ensures /tmp/attempts.txt does not exist before starting.
3. Creates a Hatchet worker, registers flaky_task, and starts it in a background thread.
4. Triggers one run of flaky_task and waits for it to complete.
5. Writes the final task output to /tmp/result.json.
6. Shuts down the worker and exits with code 0.
"""

import asyncio
import json
import os
import sys
import threading
import time

from hatchet_sdk import Hatchet

# ---------------------------------------------------------------------------
# Read required environment variables
# ---------------------------------------------------------------------------
ZEALT_RUN_ID = os.environ["ZEALT_RUN_ID"]

# ---------------------------------------------------------------------------
# Initialize Hatchet client (uses HATCHET_CLIENT_TOKEN from the environment
# and the default Cloud server endpoint — no server_url override).
# ---------------------------------------------------------------------------
hatchet = Hatchet(debug=True)

# ---------------------------------------------------------------------------
# Define flaky_task with retry + exponential backoff configuration
# ---------------------------------------------------------------------------
@hatchet.task(
    name="flaky_task",
    retries=3,
    backoff_factor=2,
    backoff_max_seconds=10,
)
def flaky_task(input, ctx):
    """
    A task that fails on the first two attempts and succeeds on the third.

    Attempt counting is persisted in /tmp/attempts.txt so the counter
    survives across Hatchet-managed retry invocations.
    """
    attempts_file = "/tmp/attempts.txt"

    # Read current attempt count (0 if file is absent or unreadable)
    try:
        with open(attempts_file, "r") as f:
            attempt = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        attempt = 0

    # Increment and persist
    attempt += 1
    with open(attempts_file, "w") as f:
        f.write(str(attempt))

    print(f"[flaky_task] attempt={attempt}", flush=True)

    # Fail until the third attempt
    if attempt < 3:
        raise RuntimeError(f"Simulated failure on attempt {attempt}; will retry.")

    # Success on attempt >= 3
    return {"status": "success", "attempt": attempt}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def main():
    # 2. Remove the attempts counter so we start fresh
    attempts_file = "/tmp/attempts.txt"
    if os.path.exists(attempts_file):
        os.remove(attempts_file)
        print(f"Removed existing {attempts_file}", flush=True)

    # 3. Create a worker with the required name and register flaky_task
    worker_name = f"task-retries-worker-{ZEALT_RUN_ID}"
    print(f"Creating worker: {worker_name}", flush=True)

    worker = hatchet.worker(worker_name, workflows=[flaky_task])

    # Start the worker in a background daemon thread.
    # worker.start() blocks (runs the asyncio event loop), so we run it in a
    # separate thread.  We save a reference to the worker's loop so we can
    # schedule a graceful shutdown later.
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    print("Worker started in background thread.", flush=True)

    # Give the worker time to connect and register with Hatchet Cloud before
    # we try to trigger a run.
    time.sleep(5)

    # 4. Trigger exactly one run of flaky_task and wait for completion.
    #    flaky_task.run() is a synchronous blocking call that returns the
    #    task's output dict once the (possibly retried) run finishes.
    print("Triggering flaky_task run...", flush=True)
    result = flaky_task.run()
    print(f"Task completed with result: {result}", flush=True)

    # 5. Write the final task output to /tmp/result.json
    result_path = "/tmp/result.json"
    with open(result_path, "w") as f:
        json.dump(result, f)
    print(f"Result written to {result_path}", flush=True)

    # 6. Shut down the worker cleanly by scheduling exit_gracefully on its
    #    event loop (the loop is running in worker_thread).
    print("Shutting down worker...", flush=True)
    worker_loop = getattr(worker, "_loop", None)
    if worker_loop is not None and worker_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            worker.exit_gracefully(), worker_loop
        )
        try:
            future.result(timeout=15)
        except Exception as e:
            print(f"Worker shutdown notice: {e}", flush=True)
    else:
        print("Worker loop not available; skipping graceful shutdown.", flush=True)

    # Wait briefly for the worker thread to finish
    worker_thread.join(timeout=10)

    print("Done. Exiting with code 0.", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
