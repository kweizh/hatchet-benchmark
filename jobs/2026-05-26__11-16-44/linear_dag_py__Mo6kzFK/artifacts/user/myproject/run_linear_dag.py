import json
import os
import threading
import time

from hatchet_sdk import Hatchet


def main() -> None:
    run_id = os.environ["ZEALT_RUN_ID"]
    workflow_name = f"linear-dag-{run_id}"

    hatchet = Hatchet()
    workflow = hatchet.workflow(name=workflow_name)

    @workflow.task()
    def step1_load(workflow_input, ctx):
        return {"text": "hello"}

    @workflow.task(parents=[step1_load])
    def step2_transform(workflow_input, ctx):
        parent_output = ctx.task_output(step1_load)
        return {"text": f"{parent_output['text']} world"}

    @workflow.task(parents=[step2_transform])
    def step3_finalize(workflow_input, ctx):
        parent_output = ctx.task_output(step2_transform)
        return {"final": f"{parent_output['text']}!"}

    worker = hatchet.worker(name=f"linear-dag-worker-{run_id}", workflows=[workflow])
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()

    time.sleep(2)

    run_result = workflow.run()
    if hasattr(run_result, "result"):
        final_output = run_result.result()
    else:
        final_output = run_result

    with open("/tmp/result.json", "w", encoding="utf-8") as result_file:
        json.dump(final_output, result_file)


if __name__ == "__main__":
    main()
