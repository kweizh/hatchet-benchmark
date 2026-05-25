# Linear DAG Workflow with Hatchet (Python)

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue and workflow engine that supports defining DAG workflows declaratively. In this task you will build a three-step linear DAG in Python where each task reads its parent's output and applies a transformation. A local Hatchet engine is already running inside the container, and `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` are already exported in the environment (they are sourced automatically from `/etc/zealt/hatchet.sh` via `BASH_ENV`).

## Requirements
- Define a Hatchet workflow named `pipeline`.
- Add three tasks to the workflow:
  - `step1`: no parent; returns the value `10`.
  - `step2`: parent is `step1`; reads the parent's value and multiplies it by `2`.
  - `step3`: parent is `step2`; reads the parent's value and adds `5`.
- Provide a worker entrypoint script that registers the workflow and runs the worker process.
- Provide a trigger script that runs the `pipeline` workflow with no input, waits for it to complete, and prints the final value produced by `step3`.

## Implementation Hints
- Use the official `hatchet-sdk` Python package (already installed).
- DAG tasks are declared with `@workflow.task(...)` and use the `parents=[...]` keyword to declare dependencies.
- Inside a child task, the parent's output is available on the `Context` object via `ctx.task_output(parent_task)`.
- For the workflow input you can use `hatchet_sdk.EmptyModel`. Task outputs can be a Pydantic `BaseModel` or a plain `dict`.
- The Hatchet client picks up `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_HOST_PORT` from the environment automatically.
- The Hatchet Python worker uses `multiprocessing` with the `spawn` start method, so the call to `worker.start()` MUST be guarded by `if __name__ == "__main__":` or it will fail with a bootstrap error.
- `pipeline.run()` blocks until the workflow finishes and returns a mapping keyed by task name (for example `{"step1": ..., "step2": ..., "step3": ...}`).
- The trigger script should print the final value on its own line using the exact format `Final output: <value>` so that automation can pick it up.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 run.py`
- The worker process must register a workflow named `pipeline` containing the three tasks `step1`, `step2`, and `step3` with the dependency chain `step1 -> step2 -> step3`.
- When the worker is running and `python3 run.py` is executed with no arguments, the trigger script must print a line matching the exact format `Final output: 25` to stdout and exit with status code `0`.

