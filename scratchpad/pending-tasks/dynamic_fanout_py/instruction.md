# Dynamic Fan-out Workflow with Hatchet (Python)

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue and workflow engine that supports spawning child tasks/workflows dynamically at runtime. In this task you will build a parent workflow that fans out work to a child workflow, with the number of children determined at runtime by the input. A local Hatchet engine is already running inside the container, and `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` are already exported in the environment (they are sourced automatically from `/etc/zealt/hatchet.sh` via `BASH_ENV`).

## Requirements
- Define a child task or workflow named `square` that takes an input with a single integer field `n` and returns a result containing the field `result` set to `n*n`.
- Define a parent workflow named `fanout` that accepts an input with a single list field `numbers` (a list of integers). In its main step, the parent must iterate over `numbers`, spawn one child run of `square` per element, wait for all child results, and return a single output object with the field `squares` containing the list of squared integers.
- The `squares` output list MUST be sorted in ascending order so that the result is deterministic regardless of child completion order.
- Provide a worker entrypoint script (`worker.py`) that registers BOTH the child and the parent and runs the Hatchet worker process.
- Provide a trigger script (`run.py`) that accepts the numbers as command-line arguments, runs the `fanout` workflow with `{"numbers": [<args>]}`, waits for completion, and prints the result.

## Implementation Hints
- Use the official `hatchet-sdk` Python package (already installed).
- A child workflow/task can be invoked from within a parent task by calling its `.aio_run(...)` method (await) or `.run(...)` (sync). For bulk spawning you can also use `aio_run_many` with `create_bulk_run_item`. See https://docs.hatchet.run/v1/child-spawning for details.
- Use Pydantic `BaseModel` for the input and output schemas (e.g., `class FanoutInput(BaseModel): numbers: list[int]`).
- The Hatchet client picks up `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_HOST_PORT` from the environment automatically.
- The Hatchet Python worker uses `multiprocessing` with the `spawn` start method, so the call to `worker.start()` MUST be guarded by `if __name__ == "__main__":` or it will fail with a bootstrap error.
- The same worker process should register both the parent and the child so that a single `python3 worker.py` is enough to handle all runs.
- The trigger script should print the aggregated list on its own line using the exact format `Squares: [<n1>, <n2>, ...]` (standard Python list repr with spaces after commas) so that automation can pick it up.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 run.py <n1> <n2> ...` (integers as positional command-line arguments)
- The worker process must register a workflow/task named `square` that takes input `{"n": <int>}` and returns output containing `{"result": <int>}` equal to the square of `n`.
- The worker process must also register a workflow named `fanout` that takes input `{"numbers": [<int>, ...]}` and returns output containing `{"squares": [<int>, ...]}` where `squares` is the sorted list of the squares of the input integers.
- When the worker is running and `python3 run.py 1 2 3 4 5` is executed, the trigger script must print a line matching the exact format `Squares: [1, 4, 9, 16, 25]` to stdout and exit with status code `0`.
- The parent workflow MUST spawn the child runs via the Hatchet child-spawning API (e.g., `child.aio_run(...)` / `aio_run_many` / `run`); it MUST NOT compute the squares locally inside the parent task body.

