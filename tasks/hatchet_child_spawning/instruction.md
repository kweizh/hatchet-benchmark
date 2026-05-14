# Hatchet Dynamic Child Spawning

## Background
Hatchet is a distributed task queue and workflow engine designed for high-concurrency, low-latency background jobs. One of its powerful features is the ability to spawn child tasks dynamically based on runtime input and wait for their completion, often used for fan-out/fan-in patterns.

## Requirements
Write a Python script using the `hatchet-sdk` package that implements a dynamic fan-out pattern:
1. Define a Pydantic model `ParentInput` containing `items: list[str]`.
2. Define a Pydantic model `ChildInput` containing `item: str`.
3. Create a child workflow named `FanoutChild` with `input_validator=ChildInput`.
4. Add a task to `FanoutChild` that takes the `ChildInput` and returns a dictionary `{"processed": input.item.upper()}`.
5. Create a parent workflow named `FanoutParent` with `input_validator=ParentInput`.
6. Add a task to `FanoutParent` (must be `async`) that spawns a `FanoutChild` for each string in `input.items` using `child_wf.aio_run_many` and `child_wf.create_bulk_run_item(input=ChildInput(item=x))`. It must wait for all children to complete and return a list of their results.
7. The script must initialize a Hatchet client, start a worker with both workflows in the background, and then trigger `FanoutParent` with `items=["apple", "banana", "cherry"]`.
8. Wait for the parent workflow to complete and write the final result (a list of dictionaries) as JSON to `/home/user/myproject/output.json`.

## Constraints
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/run.log`
- The script should be named `/home/user/myproject/main.py`.
- Ensure the worker runs in the background or a separate thread, so the script can trigger the workflow and wait for the result.
- You must use the `HATCHET_CLIENT_TOKEN` environment variable for authentication (it will be provided in the environment).

## Integrations
- None