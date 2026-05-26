"""Standalone worker script - run this in the background."""
import os

from hatchet_sdk import Context, Hatchet

run_id = os.environ["ZEALT_RUN_ID"]
workflow_name = f"linear-dag-{run_id}"

hatchet = Hatchet()

wf = hatchet.workflow(name=workflow_name)


@wf.task()
def step1_load(input, ctx: Context):
    return {"text": "hello"}


@wf.task(parents=[step1_load])
def step2_transform(input, ctx: Context):
    parent_output = ctx.task_output(step1_load)
    # parent_output is an EmptyModel (with extra="allow"), access fields as attributes
    text = parent_output.text
    return {"text": f"{text} world"}


@wf.task(parents=[step2_transform])
def step3_finalize(input, ctx: Context):
    parent_output = ctx.task_output(step2_transform)
    # parent_output is an EmptyModel (with extra="allow"), access fields as attributes
    text = parent_output.text
    return {"final": f"{text}!"}


if __name__ == "__main__":
    worker = hatchet.worker(f"linear-dag-worker-{run_id}", workflows=[wf])
    worker.start()
