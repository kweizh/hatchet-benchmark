from __future__ import annotations

from pydantic import BaseModel
from hatchet_sdk import Hatchet

hatchet = Hatchet()


class SquareItemInput(BaseModel):
    item: int


square_item_workflow = hatchet.workflow(
    name="square_item",
    input_validator=SquareItemInput,
)


@square_item_workflow.task()
def square_item(input: SquareItemInput, ctx):
    return {"square": input.item * input.item}


class ProcessBatchInput(BaseModel):
    items: list[int]


process_batch_workflow = hatchet.workflow(
    name="process_batch",
    input_validator=ProcessBatchInput,
)


@process_batch_workflow.task()
def process_batch(input: ProcessBatchInput, ctx):
    bulk_items = [
        square_item_workflow.create_bulk_run_item(
            SquareItemInput(item=item),
            key=f"item-{index}",
        )
        for index, item in enumerate(input.items)
    ]

    results = square_item_workflow.run_many(bulk_items)
    squares = [result["square_item"]["square"] for result in results]

    return {"squares": squares}
