# Diamond / Multi-Parent DAG Workflow with Hatchet (Python)

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue and workflow engine that supports defining DAG workflows declaratively. Beyond linear chains, Hatchet schedules independent tasks in parallel and lets a child task consume outputs from **multiple** parents via its `Context`. In this task you will build a diamond-shaped DAG in Python: one root task fans out into two parallel branches, which then join into a single final task. A local Hatchet engine is already running inside the container, and `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` are already exported in the environment (they are sourced automatically from `/etc/zealt/hatchet.sh` via `BASH_ENV`).

## Requirements
- Define a Hatchet workflow named `diamond`.
- Add four tasks to the workflow forming a diamond shape:
  - `step_root`: no parent; returns a value of `10` under the key `base`.
  - `step_left`: parent is `step_root`; reads the parent's `base` value and returns `base * 2` under the key `value`.
  - `step_right`: parent is `step_root`; reads the parent's `base` value and returns `base + 7` under the key `value`.
  - `step_join`: parents are `step_left` AND `step_right`; reads both parents' `value` outputs and returns their sum under the key `sum`.
- The two middle tasks (`step_left` and `step_right`) must be defined as independent siblings so that Hatchet can run them in parallel.
- Provide a worker entrypoint script that registers the workflow and runs the worker process.
- Provide a trigger script that runs the `diamond` workflow with no input, waits for it to complete, and prints the final sum produced by `step_join`.

## Implementation Hints
- Use the official `hatchet-sdk` Python package (already installed).
- DAG tasks are declared with `@workflow.task(...)`; multi-parent dependencies are declared with `parents=[parent_a, parent_b]`.
- Inside a child task, each parent's output is available on the `Context` object via `ctx.task_output(parent_task)`.
- For the workflow input you can use `hatchet_sdk.EmptyModel`. Task outputs can be a Pydantic `BaseModel` or a plain `dict`.
- The Hatchet client picks up `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_HOST_PORT` from the environment automatically.
- The Hatchet Python worker uses `multiprocessing` with the `spawn` start method, so the call to `worker.start()` MUST be guarded by `if __name__ == "__main__":` or it will fail with a bootstrap error.
- `diamond.run()` blocks until the workflow finishes and returns a mapping keyed by task name (for example `{"step_root": ..., "step_left": ..., "step_right": ..., "step_join": ...}`).
- The trigger script should print the final value on its own line using the exact format `Final sum: <value>` so that automation can pick it up.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 run.py`
- The worker process must register a workflow named `diamond` containing the four tasks `step_root`, `step_left`, `step_right`, and `step_join` with the dependency structure `step_root -> {step_left, step_right} -> step_join`.
- When the worker is running and `python3 run.py` is executed with no arguments, the trigger script must print a line matching the exact format `Final sum: 37` to stdout and exit with status code `0`.

