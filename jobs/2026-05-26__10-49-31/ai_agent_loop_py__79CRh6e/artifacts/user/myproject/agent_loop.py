#!/usr/bin/env python3
"""
Hatchet Durable Agent Loop
Runs a durable task that simulates an AI agent loop with 5 iterations,
persisting state to /tmp/agent_state.json and using durable sleeps.
"""

import json
import os
import sys
import threading
import time
from datetime import timedelta

from hatchet_sdk import EmptyModel, Hatchet
from hatchet_sdk.context.context import DurableContext

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
STATE_FILE = "/tmp/agent_state.json"
RESULT_FILE = "/tmp/result.json"

hatchet = Hatchet()


# ---------------------------------------------------------------------------
# Durable task definition
# ---------------------------------------------------------------------------
@hatchet.durable_task(
    name="agent_loop",
    execution_timeout=timedelta(minutes=5),
)
async def agent_loop(input: EmptyModel, ctx: DurableContext) -> dict:
    """
    Durable agent loop that runs for 5 iterations.
    Each iteration:
      1. Reads state from /tmp/agent_state.json
      2. Increments step
      3. Appends a thought to history
      4. Writes state back
      5. Sleeps durably for 1 second
    """
    # Initialize state file if it doesn't exist
    if not os.path.exists(STATE_FILE):
        state = {"step": 0, "history": []}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    while True:
        # 1. Read current state
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

        # Check if we've already completed
        if state["step"] >= 5:
            break

        # 2. Increment step
        state["step"] += 1

        # 3. Append thought
        state["history"].append({"thought": f"iter {state['step']}"})

        # 4. Write updated state
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

        # 5. Durable sleep (yields back to Hatchet)
        await ctx.aio_sleep_for(timedelta(seconds=1))

        # Exit condition
        if state["step"] >= 5:
            break

    # Read final state
    with open(STATE_FILE, "r") as f:
        final_state = json.load(f)

    return {
        "final_step": final_state["step"],
        "history_length": len(final_state["history"]),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def main() -> None:
    run_id = os.environ.get("ZEALT_RUN_ID", "default")

    # Clean up any pre-existing files
    for path in [STATE_FILE, RESULT_FILE]:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed pre-existing file: {path}")

    worker_name = f"ai-agent-loop-worker-{run_id}"
    print(f"Starting worker: {worker_name}")

    # Create worker with the durable task registered
    worker = hatchet.worker(
        name=worker_name,
        workflows=[agent_loop],
    )

    # Start the worker in a background thread (worker.start() blocks the loop)
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()

    # Give the worker a moment to connect and register
    print("Waiting for worker to connect...")
    time.sleep(3)

    # Trigger the task and wait for the result
    print("Triggering agent_loop task...")
    result = agent_loop.run(input=EmptyModel(), wait_for_result=True)

    print(f"Task completed. Result: {result}")

    # Write result to /tmp/result.json
    with open(RESULT_FILE, "w") as f:
        json.dump(result, f)
    print(f"Result written to {RESULT_FILE}")

    # Verify state file
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    print(f"Final state: {state}")

    # Shut down the worker
    print("Shutting down worker...")
    import asyncio

    loop = worker._loop  # access internal loop to schedule graceful exit
    if loop and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            worker.exit_gracefully(), loop
        )
        try:
            future.result(timeout=10)
        except Exception as e:
            print(f"Worker shutdown warning: {e}")

    print("Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()
