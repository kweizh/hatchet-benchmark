#!/usr/bin/env python3
"""
Hatchet heartbeat runner.

Steps:
  1. Read ZEALT_RUN_ID from environment.
  2. Define a heartbeat task that appends a UTC ISO-8601 timestamp to
     /tmp/heartbeats.log.
  3. Start a Hatchet worker in a background thread.
  4. Create a cron trigger (every minute) for the heartbeat task.
  5. Wait ~75 seconds so at least one cron-fired run can execute.
  6. Stop the worker cleanly.
  7. Delete the cron trigger.
  8. Exit 0.
"""

import asyncio
import os
import sys
import time
import threading
from datetime import datetime, timezone

from hatchet_sdk import Context, Hatchet

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

run_id = os.environ.get("ZEALT_RUN_ID")
if not run_id:
    print("ERROR: ZEALT_RUN_ID environment variable is not set.", flush=True)
    sys.exit(1)

print(f"[runner] ZEALT_RUN_ID={run_id}", flush=True)

# Initialise the Hatchet client.
# Authentication comes from HATCHET_CLIENT_TOKEN in the environment.
# No server address is set; the SDK's built-in default points at Hatchet Cloud.
hatchet = Hatchet(debug=True)

TASK_NAME = f"heartbeat-{run_id}"
CRON_NAME = f"hb-cron-{run_id}"
HEARTBEAT_LOG = "/tmp/heartbeats.log"

# ---------------------------------------------------------------------------
# Task definition
# ---------------------------------------------------------------------------


@hatchet.task(name=TASK_NAME)
def heartbeat(input, ctx: Context) -> dict:
    """Append a UTC ISO-8601 timestamp to the heartbeat log file."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(HEARTBEAT_LOG, "a") as f:
        f.write(timestamp + "\n")
    print(f"[heartbeat] wrote timestamp: {timestamp}", flush=True)
    return {"timestamp": timestamp}


# ---------------------------------------------------------------------------
# Worker management
# ---------------------------------------------------------------------------

_worker = None  # Will be set before the thread starts


def run_worker() -> None:
    """Run the Hatchet worker (blocking). Called from a daemon thread."""
    _worker.start()  # blocks until the event loop is stopped


def start_worker_thread() -> threading.Thread:
    """Create the worker, spin up its thread, and return the thread."""
    global _worker
    _worker = hatchet.worker(
        name=f"heartbeat-worker-{run_id}",
        workflows=[heartbeat],
    )
    t = threading.Thread(target=run_worker, daemon=True, name="hatchet-worker")
    t.start()
    return t


def stop_worker() -> None:
    """Ask the worker to exit gracefully by scheduling the coroutine on its loop."""
    global _worker
    if _worker is None:
        return
    loop = _worker._loop
    if loop is not None and loop.is_running():
        asyncio.run_coroutine_threadsafe(_worker.exit_gracefully(), loop)
        print("[runner] exit_gracefully() scheduled on worker loop.", flush=True)
    else:
        print("[runner] Worker loop not running; skipping graceful stop.", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("[runner] Starting worker thread …", flush=True)
    worker_thread = start_worker_thread()

    # Give the worker a moment to register with Hatchet Cloud before we create
    # the cron trigger, so the triggered run will be picked up immediately.
    print("[runner] Waiting 5 s for worker to register …", flush=True)
    time.sleep(5)

    # --- Create the cron trigger ---
    print(
        f"[runner] Creating cron trigger '{CRON_NAME}' for workflow '{TASK_NAME}' …",
        flush=True,
    )
    cron_trigger = hatchet.cron.create(
        workflow_name=TASK_NAME,
        cron_name=CRON_NAME,
        expression="* * * * *",
        input={},
        additional_metadata={},
    )
    cron_id = cron_trigger.metadata.id
    print(f"[runner] Cron trigger created: id={cron_id}", flush=True)

    # --- Wait for the every-minute cron to fire at least once ---
    # 75 seconds guarantees we cross at least one wall-clock minute boundary.
    print("[runner] Waiting 75 s for cron to fire …", flush=True)
    time.sleep(75)

    # --- Stop the worker ---
    print("[runner] Stopping worker …", flush=True)
    stop_worker()
    worker_thread.join(timeout=15)
    print("[runner] Worker thread joined.", flush=True)

    # --- Delete the cron trigger ---
    print(f"[runner] Deleting cron trigger id={cron_id} …", flush=True)
    hatchet.cron.delete(cron_id=cron_id)
    print("[runner] Cron trigger deleted.", flush=True)

    print("[runner] Done. Exiting 0.", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
