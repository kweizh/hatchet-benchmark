"""Diamond-shaped parallel DAG workflow definition."""
from hatchet_sdk import Context, Hatchet

hatchet = Hatchet()

workflow = hatchet.workflow(name="diamond-dag")


@workflow.task()
def start(input, ctx: Context) -> dict:
    return {"value": 10}


@workflow.task(parents=[start])
def branch_a(input, ctx: Context) -> dict:
    start_output = ctx.task_output(start)
    return {"a": start_output["value"] * 2}


@workflow.task(parents=[start])
def branch_b(input, ctx: Context) -> dict:
    start_output = ctx.task_output(start)
    return {"b": start_output["value"] + 5}


@workflow.task(parents=[branch_a, branch_b])
def merge(input, ctx: Context) -> dict:
    a_output = ctx.task_output(branch_a)
    b_output = ctx.task_output(branch_b)
    return {"sum": a_output["a"] + b_output["b"]}
