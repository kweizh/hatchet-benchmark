"""
Dynamic fan-out pipeline using Hatchet Python SDK.

- square_item  (child):  receives {"item": int}, returns {"square": int*int}
- process_batch (parent): receives {"items": [int, ...]},
                          spawns one square_item child per element,
                          aggregates results preserving order,
                          returns {"squares": [int, ...]}
"""

from __future__ import annotations

from pydantic import BaseModel

from hatchet_sdk import Context, Hatchet

hatchet = Hatchet(debug=True)


# ── input models ─────────────────────────────────────────────────────────────

class SquareItemInput(BaseModel):
    item: int


class ProcessBatchInput(BaseModel):
    items: list[int]


# ── child workflow: square_item ───────────────────────────────────────────────

square_item = hatchet.workflow(
    name="square_item",
    input_validator=SquareItemInput,
)


@square_item.task(name="square_item")
async def do_square(input: SquareItemInput, ctx: Context) -> dict:
    return {"square": input.item * input.item}


# ── parent workflow: process_batch ────────────────────────────────────────────

process_batch = hatchet.workflow(
    name="process_batch",
    input_validator=ProcessBatchInput,
)


@process_batch.task(name="process_batch")
async def do_process_batch(input: ProcessBatchInput, ctx: Context) -> dict:
    """Fan out: spawn one square_item child per element, then collect in order."""

    # Build bulk run items — one per element, keyed by index for ordering
    bulk_items = [
        square_item.create_bulk_run_item(
            input=SquareItemInput(item=value),
            child_key=str(idx),          # stable dedup key
        )
        for idx, value in enumerate(input.items)
    ]

    # Spawn all children and await ALL of them concurrently; results come back
    # in the same order as bulk_items.
    # Each result is a dict keyed by task-name -> task-output, e.g.
    #   {"square_item": {"square": 4}}
    results: list[dict] = await square_item.aio_run_many(
        bulk_items,
        wait_for_result=True,
    )

    squares = [r["square_item"]["square"] for r in results]
    return {"squares": squares}
