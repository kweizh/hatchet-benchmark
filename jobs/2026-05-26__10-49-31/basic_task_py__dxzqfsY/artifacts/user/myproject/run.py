#!/usr/bin/env python3
"""
Hatchet basic task runner: defines simple_greeting task, runs it against
Hatchet Cloud, writes result to /tmp/result.json, and exits cleanly.
"""

import asyncio
import json
import os
import threading

from pydantic import BaseModel

from hatchet_sdk import Hatchet

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ZEALT_RUN_ID = os.environ["ZEALT_RUN_ID"]
WORKER_NAME = f"basic-task-worker-{ZEALT_RUN_ID}"
RESULT_PATH = "/tmp/result.json"

# ---------------------------------------------------------------------------
# Hatchet client (reads HATCHET_CLIENT_TOKEN from environment automatically)
# ---------------------------------------------------------------------------

hatchet = Hatchet()

# ---------------------------------------------------------------------------
# Task input/output models
# ---------------------------------------------------------------------------


class GreetingInput(BaseModel):
    name: str


class GreetingOutput(BaseModel):
    greeting: str


# ---------------------------------------------------------------------------
# Task definition
# ---------------------------------------------------------------------------


@hatchet.task(name="simple_greeting", input_validator=GreetingInput)
def simple_greeting(input: GreetingInput, ctx) -> GreetingOutput:
    return GreetingOutput(greeting=f"Hello, {input.name}!")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_worker(worker):
    """Run the worker in a dedicated thread (blocks until stopped)."""
    worker.start()


def main():
    # Create and configure the worker
    worker = hatchet.worker(
        name=WORKER_NAME,
        workflows=[simple_greeting],
    )

    # Start the worker in a background thread so we can trigger a run
    worker_thread = threading.Thread(target=run_worker, args=(worker,), daemon=True)
    worker_thread.start()

    # Give the worker a moment to connect and register
    import time
    time.sleep(5)

    # Trigger the task and wait for its result (synchronous blocking call)
    result = simple_greeting.run(GreetingInput(name="World"))

    # result is a GreetingOutput (pydantic model) or a plain dict
    if isinstance(result, BaseModel):
        result_dict = result.model_dump()
    elif isinstance(result, dict):
        result_dict = result
    else:
        # fallback: try to coerce
        result_dict = {"greeting": str(result)}

    # Write result to /tmp/result.json
    with open(RESULT_PATH, "w") as f:
        json.dump(result_dict, f)

    print(f"Result written to {RESULT_PATH}: {result_dict}")

    # Shut down the worker gracefully by scheduling exit_gracefully on its loop
    if worker._loop and worker._loop.is_running():
        asyncio.run_coroutine_threadsafe(worker.exit_gracefully(), worker._loop)
        # Wait briefly for the worker thread to stop
        worker_thread.join(timeout=10)

    print("Done. Exiting.")


if __name__ == "__main__":
    main()
