"""
Runner script for the delayed_greeting durable task.

The Hatchet worker uses multiprocessing with the 'spawn' start method, which
requires all top-level code that creates processes to live inside the
``if __name__ == '__main__':`` guard.  The task definition itself is safe at
module level because the spawned child imports this module but only runs the
action-listener bootstrap, not the worker-start code.

Strategy:
  1. Build a Hatchet client (reads HATCHET_CLIENT_TOKEN from env).
  2. Define the ``delayed_greeting`` durable task.
  3. Inside __main__: start a worker in a background thread so worker.start()
     can block its own event loop without blocking the main thread.
  4. Wait briefly for the worker and its action-listener subprocess to register
     with Hatchet Cloud, then call task.run() which blocks until done.
  5. Write the result to /tmp/result.json and exit 0.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone

from hatchet_sdk import Hatchet
from hatchet_sdk.context.context import DurableContext
from hatchet_sdk.runnables.types import EmptyModel

# ---------------------------------------------------------------------------
# Hatchet client – safe at module level (no subprocess spawning here)
# ---------------------------------------------------------------------------
hatchet = Hatchet()

# ---------------------------------------------------------------------------
# Durable task definition – also safe at module level
# ---------------------------------------------------------------------------
@hatchet.durable_task(
    name="delayed_greeting",
    execution_timeout=timedelta(minutes=5),
)
async def delayed_greeting(input: EmptyModel, ctx: DurableContext) -> dict:
    """Sleep durably for ~5 seconds and return elapsed wall-clock seconds."""
    # Durable, memoised wall-clock timestamp (safe across replays)
    start: datetime = await ctx.aio_now()

    # Durable sleep – NOT time.sleep / asyncio.sleep
    await ctx.aio_sleep_for(timedelta(seconds=5))

    end: datetime = datetime.now(tz=timezone.utc)
    elapsed_sec = int((end - start).total_seconds())

    return {"message": "wakeup", "elapsed_sec": elapsed_sec}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Build the worker (no subprocess spawned yet)
    worker = hatchet.worker(
        name="delayed-greeting-worker",
        workflows=[delayed_greeting],
        durable_slots=10,
    )

    # --- Background thread to run the blocking worker.start() ---
    _worker_started = threading.Event()
    _worker_exception: list[BaseException] = []

    def _run_worker() -> None:
        """Runs in a background daemon thread; worker.start() blocks here."""
        try:
            # Patch _setup_loop to signal readiness once the event loop exists.
            _original_setup = worker._setup_loop

            def _patched_setup() -> None:
                _original_setup()
                _worker_started.set()

            worker._setup_loop = _patched_setup
            worker.start()
        except Exception as exc:  # noqa: BLE001
            _worker_exception.append(exc)
            _worker_started.set()  # unblock main thread even on error

    _thread = threading.Thread(target=_run_worker, daemon=True, name="hatchet-worker")
    _thread.start()

    # --- Wait for the event loop to be created ---
    print("Waiting for worker event loop to start…")
    if not _worker_started.wait(timeout=30):
        raise RuntimeError("Worker did not start within 30 seconds")

    if _worker_exception:
        raise _worker_exception[0]

    # Give the spawned action-listener subprocess time to connect and register
    # with Hatchet Cloud before we push a task.
    print("Waiting for action listener to register with Hatchet Cloud…")
    time.sleep(5)

    # --- Trigger the durable task and block until done ---
    print("Triggering delayed_greeting task…")
    result: dict = delayed_greeting.run()
    print(f"Task result: {result}")

    # --- Write result file ---
    output_path = "/tmp/result.json"
    with open(output_path, "w") as fh:
        json.dump(result, fh)
    print(f"Result written to {output_path}")

    # --- Graceful shutdown ---
    if worker._loop and not worker._loop.is_closed():
        import asyncio
        asyncio.run_coroutine_threadsafe(worker.exit_gracefully(), worker._loop)

    # Let the shutdown coroutine run, then force-exit cleanly.
    time.sleep(2)
    os._exit(0)
