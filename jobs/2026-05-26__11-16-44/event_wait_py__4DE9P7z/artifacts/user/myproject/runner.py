import asyncio
import json
import os
import threading
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


def build_workflow(hatchet: Hatchet):
    workflow = hatchet.workflow(name="onboarding_flow", input_validator=EmptyModel)

    @workflow.durable_task(name="onboarding_flow")
    async def onboarding_flow(_: EmptyModel, ctx: DurableContext):
        with open("/tmp/events.log", "a", encoding="utf-8") as log_file:
            log_file.write("onboarding_flow started\n")

        conditions = or_(
            SleepCondition(duration=timedelta(seconds=30)),
            UserEventCondition(event_key="user:profile_completed"),
        )

        result = await ctx.aio_wait_for("onboarding_flow_wait", conditions)
        resolved = result.get("CREATE", {})

        if "user:profile_completed" in resolved:
            return {"status": "completed_via_event"}

        return {"status": "completed_via_timeout"}

    return workflow


def start_worker(worker):
    worker.start()


def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        raise RuntimeError("ZEALT_RUN_ID is required")

    hatchet = Hatchet()
    workflow = build_workflow(hatchet)
    worker_name = f"event-wait-worker-{run_id}"

    worker = hatchet.worker(name=worker_name, workflows=[workflow])
    worker_thread = threading.Thread(target=start_worker, args=(worker,), daemon=True)
    worker_thread.start()

    time.sleep(2)

    run_ref = workflow.run_no_wait()

    time.sleep(5)
    hatchet.event.push("user:profile_completed", {})

    result = run_ref.result()
    output = result.get("onboarding_flow", result)
    with open("/tmp/result.json", "w", encoding="utf-8") as result_file:
        json.dump(output, result_file)

    if worker.loop is not None:
        close_future = asyncio.run_coroutine_threadsafe(worker._close(), worker.loop)
        close_future.result(timeout=30)
        worker.loop.call_soon_threadsafe(worker.loop.stop)

    worker_thread.join(timeout=30)


if __name__ == "__main__":
    main()
