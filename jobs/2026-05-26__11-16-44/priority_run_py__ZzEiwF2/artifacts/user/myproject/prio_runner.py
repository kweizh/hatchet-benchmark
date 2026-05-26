import asyncio
import os
import threading
import time
from typing import List

from hatchet_sdk import Hatchet


def main() -> None:
    run_id = os.environ["ZEALT_RUN_ID"]
    workflow_name = f"prio-task-{run_id}"
    log_path = f"/tmp/prio_log_{run_id}.txt"

    with open(log_path, "w", encoding="utf-8"):
        pass

    hatchet = Hatchet()
    workflow = hatchet.workflow(name=workflow_name, default_priority=1)

    @workflow.task(name=workflow_name)
    def prio_task(_: dict, ctx) -> dict:
        priority = ctx.priority or 1
        epoch_ms = int(time.time() * 1000)
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{priority} {epoch_ms}\n")
        time.sleep(2)
        return {"priority": priority, "epoch_ms": epoch_ms}

    worker = hatchet.worker(
        name=f"prio-worker-{run_id}",
        slots=1,
        workflows=[workflow],
    )

    worker_thread = threading.Thread(target=worker.start, name="hatchet-worker")
    worker_thread.daemon = True
    worker_thread.start()

    time.sleep(2)

    try:
        run_refs: List = []
        for _ in range(3):
            run_refs.append(workflow.run_no_wait(priority=1))
        for _ in range(2):
            run_refs.append(workflow.run_no_wait(priority=3))

        for run_ref in run_refs:
            run_ref.result()
    finally:
        if worker._loop is not None:
            try:
                close_future = asyncio.run_coroutine_threadsafe(
                    worker._close(), worker._loop
                )
                close_future.result(timeout=10)
            except Exception:
                pass
            worker._loop.call_soon_threadsafe(worker._loop.stop)

        worker_thread.join(timeout=10)


if __name__ == "__main__":
    main()
