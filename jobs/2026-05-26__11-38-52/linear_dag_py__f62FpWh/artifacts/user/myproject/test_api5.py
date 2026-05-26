from hatchet_sdk import Hatchet, Context
import os

hatchet = Hatchet()
workflow = hatchet.workflow(name="test")

@workflow.task()
def step1_load(ctx: Context):
    return {"text": "hello"}

@workflow.task(parents=[step1_load])
def step2_transform(ctx: Context):
    return {"text": ctx.task_output(step1_load)["text"] + " world"}

print("Success!")
