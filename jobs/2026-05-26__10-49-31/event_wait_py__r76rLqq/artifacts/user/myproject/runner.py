#!/usr/bin/env python3
"""
Hatchet Durable Event Wait Runner

Defines an `onboarding_flow` durable task that waits for either:
  1. A `user:profile_completed` event, or
  2. A 30-second sleep timeout

Then triggers the workflow, pushes the event ~5 seconds later,
waits for the result, writes it to /tmp/result.json, and exits.
"""

import asyncio
import json
import multiprocessing
import os
import sys
import time
from datetime import timedelta

from hatchet_sdk import (
    DurableContext,
    EmptyModel,
    Hatchet,
    SleepCondition,
    UserEventCondition,
    or_,
)

# ---------------------------------------------------------------------------
# Read required env vars
# ---------------------------------------------------------------------------
ZEALT_RUN_ID = os.environ["ZEALT_RUN_ID"]
WORKER_NAME = f"event-wait-worker-{ZEALT_RUN_ID}"


# ---------------------------------------------------------------------------
# Worker process entry point (runs in a separate process)
# ---------------------------------------------------------------------------
def worker_process_main(worker_name: str) -> None:
    """Run the Hatchet worker in a dedicated process."""
    from hatchet_sdk import (
        DurableContext,
        EmptyModel,
        Hatchet,
        SleepCondition,
        UserEventCondition,
        or_,
    )
    from datetime import timedelta

    hatchet = Hatchet()

    @hatchet.durable_task(
        name="onboarding_flow",
        execution_timeout=timedelta(seconds=120),
    )
    async def onboarding_flow(input: EmptyModel, ctx: DurableContext) -> dict:
        # First action: append to /tmp/events.log
        with open("/tmp/events.log", "a") as f:
            f.write("onboarding_flow started\n")

        # Wait for either the user event OR a 30-second sleep, whichever comes first
        result = await ctx.aio_wait_for(
            "wait-for-profile-or-timeout",
            or_(
                SleepCondition(duration=timedelta(seconds=30)),
                UserEventCondition(event_key="user:profile_completed"),
            ),
        )

        # Inspect which condition resolved.
        # result is shaped like {"CREATE": {"<condition_key>": ...}}
        resolved_keys: set = set()
        for group_result in result.values():
            if isinstance(group_result, dict):
                resolved_keys.update(group_result.keys())

        if "user:profile_completed" in resolved_keys:
            return {"status": "completed_via_event"}
        else:
            return {"status": "completed_via_timeout"}

    worker = hatchet.worker(
        worker_name,
        durable_slots=10,
        workflows=[onboarding_flow],
    )
    worker.start()


# ---------------------------------------------------------------------------
# Main async logic (runs in the parent process)
# ---------------------------------------------------------------------------
async def main() -> None:
    # ---------------------------------------------------------------------------
    # Create the Hatchet client for triggering and event pushing
    # (uses HATCHET_CLIENT_TOKEN from env, default cloud endpoint)
    # ---------------------------------------------------------------------------
    hatchet = Hatchet()

    # Also define the workflow stub here so we can trigger it
    @hatchet.durable_task(
        name="onboarding_flow",
        execution_timeout=timedelta(seconds=120),
    )
    async def onboarding_flow(input: EmptyModel, ctx: DurableContext) -> dict:
        # This definition is only used for triggering — the actual execution
        # happens in the worker process.
        return {}

    # Start worker in a separate process
    print(f"Starting worker process '{WORKER_NAME}'...", flush=True)
    ctx = multiprocessing.get_context("spawn")
    proc = ctx.Process(
        target=worker_process_main,
        args=(WORKER_NAME,),
        daemon=False,
    )
    proc.start()
    print(f"Worker process PID: {proc.pid}", flush=True)

    # Give the worker time to connect and register with Hatchet Cloud
    await asyncio.sleep(10)
    print("Worker should be ready, triggering workflow run...", flush=True)

    # Trigger exactly one run of onboarding_flow (non-blocking — returns a ref)
    ref = await onboarding_flow.aio_run(wait_for_result=False)
    print(f"Workflow run triggered: {ref}", flush=True)

    # Wait ~5 seconds, then push the user:profile_completed event
    await asyncio.sleep(5)
    print("Pushing user:profile_completed event...", flush=True)
    await hatchet.event.aio_push("user:profile_completed", {})
    print("Event pushed.", flush=True)

    # Wait for the workflow run to complete and collect the result
    print("Waiting for workflow run result...", flush=True)
    output = await ref.aio_result()
    print(f"Workflow completed: {output}", flush=True)

    # The result dict has the task name as top-level key; unwrap if present
    task_result = output.get("onboarding_flow", output)

    # Write the result to /tmp/result.json
    with open("/tmp/result.json", "w") as f:
        json.dump(task_result, f)
    print(f"Result written to /tmp/result.json: {task_result}", flush=True)

    # Terminate the worker process cleanly
    print("Terminating worker process...", flush=True)
    proc.terminate()
    proc.join(timeout=10)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=5)
    print("Worker process terminated. Exiting.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
