import json
import multiprocessing
import time

from hatchet_sdk import Hatchet, Context


def main() -> None:
    hatchet = Hatchet()
    workflow = hatchet.workflow(name="diamond-dag")

    @workflow.task(name="start")
    def start(_: dict, ctx: Context) -> dict:
        return {"value": 10}

    @workflow.task(name="branch_a", parents=[start])
    def branch_a(_: dict, ctx: Context) -> dict:
        start_output = ctx.task_output(start)
        return {"a": start_output["value"] * 2}

    @workflow.task(name="branch_b", parents=[start])
    def branch_b(_: dict, ctx: Context) -> dict:
        start_output = ctx.task_output(start)
        return {"b": start_output["value"] + 5}

    @workflow.task(name="merge", parents=[branch_a, branch_b])
    def merge(_: dict, ctx: Context) -> dict:
        branch_a_output = ctx.task_output(branch_a)
        branch_b_output = ctx.task_output(branch_b)
        return {"sum": branch_a_output["a"] + branch_b_output["b"]}

    worker = hatchet.worker("diamond-worker", workflows=[workflow])
    worker_process = multiprocessing.Process(target=worker.start, daemon=True)
    worker_process.start()

    time.sleep(1)
    run_result = workflow.run()
    merge_output = run_result.get("merge", {})

    with open("/tmp/result.json", "w", encoding="utf-8") as handle:
        json.dump(merge_output, handle)

    worker_process.terminate()
    worker_process.join(timeout=5)


if __name__ == "__main__":
    main()
