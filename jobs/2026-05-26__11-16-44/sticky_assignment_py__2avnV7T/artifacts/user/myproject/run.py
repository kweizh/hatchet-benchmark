import json
import os
import signal
import socket
import time
from multiprocessing import get_context
from typing import Dict

from hatchet_sdk import Context, EmptyModel, Hatchet, StickyStrategy

LOG_PATH = "/tmp/run_steps.log"
RESULT_PATH = "/tmp/result.json"


def append_log(step_name: str) -> Dict[str, str]:
    worker_id = os.environ.get("WORKER_ID", "unknown")
    hostname = socket.gethostname()
    pid = os.getpid()
    line = f"step={step_name} worker_id={worker_id} hostname={hostname} pid={pid}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return {"worker_id": worker_id}


def build_workflow(hatchet: Hatchet, workflow_name: str):
    workflow = hatchet.workflow(name=workflow_name, sticky=StickyStrategy.SOFT)

    @workflow.task(name="step_a")
    def step_a(input: EmptyModel, ctx: Context) -> Dict[str, str]:
        return append_log("step_a")

    @workflow.task(name="step_b", parents=[step_a])
    def step_b(input: EmptyModel, ctx: Context) -> Dict[str, str]:
        _ = ctx.task_output(step_a)
        return append_log("step_b")

    @workflow.task(name="step_c", parents=[step_b])
    def step_c(input: EmptyModel, ctx: Context) -> Dict[str, str]:
        _ = ctx.task_output(step_b)
        return append_log("step_c")

    return workflow


def worker_process(worker_id: str, workflow_name: str) -> None:
    os.environ["WORKER_ID"] = worker_id
    hatchet = Hatchet()
    workflow = build_workflow(hatchet, workflow_name)
    worker = hatchet.worker(worker_id, workflows=[workflow])
    worker.start()


def parse_worker_ids() -> list[str]:
    worker_ids_by_step: Dict[str, str] = {}
    with open(LOG_PATH, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = dict(part.split("=", 1) for part in line.strip().split(" ") if "=" in part)
            step = parts.get("step")
            worker_id = parts.get("worker_id")
            if step and worker_id:
                worker_ids_by_step[step] = worker_id

    return [
        worker_ids_by_step.get("step_a", ""),
        worker_ids_by_step.get("step_b", ""),
        worker_ids_by_step.get("step_c", ""),
    ]


def main() -> None:
    run_id = os.environ.get("ZEALT_RUN_ID", "local")
    workflow_name = f"sticky-dag-{run_id}"

    with open(LOG_PATH, "w", encoding="utf-8"):
        pass

    worker_a_id = f"worker-A-{run_id}"
    worker_b_id = f"worker-B-{run_id}"

    ctx = get_context("spawn")
    worker_a = ctx.Process(target=worker_process, args=(worker_a_id, workflow_name))
    worker_b = ctx.Process(target=worker_process, args=(worker_b_id, workflow_name))

    worker_a.start()
    worker_b.start()

    try:
        time.sleep(4)

        hatchet = Hatchet()
        workflow = build_workflow(hatchet, workflow_name)
        workflow.run(EmptyModel())

        worker_ids = parse_worker_ids()
        with open(RESULT_PATH, "w", encoding="utf-8") as handle:
            json.dump({"worker_ids": worker_ids}, handle)
    finally:
        for proc in (worker_a, worker_b):
            if proc.is_alive():
                proc.terminate()
        for proc in (worker_a, worker_b):
            proc.join(timeout=10)
            if proc.is_alive():
                os.kill(proc.pid, signal.SIGKILL)


if __name__ == "__main__":
    main()
