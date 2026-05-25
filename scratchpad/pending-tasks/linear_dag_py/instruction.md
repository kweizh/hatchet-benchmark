# Linear DAG Workflow with Hatchet Python SDK

## Background
Hatchet is a distributed task queue and workflow engine that supports building durable DAGs (Directed Acyclic Graphs). In a DAG, child tasks can read their parent tasks' outputs via the runtime `Context` object, and Hatchet schedules tasks in dependency order on a connected worker.

You will build a small linear DAG with the Hatchet Python SDK (`hatchet-sdk`), register it on a worker connected to Hatchet Cloud, trigger a run, and persist the final result to disk.

## Requirements
- Use the `hatchet-sdk` Python package to build a single DAG workflow with **exactly three tasks** that run **strictly sequentially** (each task is the parent of the next).
- The three tasks must be declared with these task names (the function/Python identifiers, as accepted by the `@workflow.task(...)` decorator):
  1. `step1_load` - takes no meaningful input and returns `{"text": "hello"}`.
  2. `step2_transform` - declares `step1_load` as its parent. It must read the parent's output via the Hatchet `Context` (using `ctx.task_output(step1_load)`) and return `{"text": "<step1_text> world"}`, where `<step1_text>` is the `text` value from `step1_load`'s output (i.e., the literal string `hello world` for this run).
  3. `step3_finalize` - declares `step2_transform` as its parent. It must read the parent's output via the Hatchet `Context` (using `ctx.task_output(step2_transform)`) and return `{"final": "<step2_text>!"}` (i.e., the literal string `hello world!` for this run).
- Connect to **Hatchet Cloud** (the default Hatchet server). Do not configure a custom server address. Authenticate with the `HATCHET_CLIENT_TOKEN` environment variable, which is already set in the environment.
- The workflow must be **registered on and executed by a real Hatchet worker** process connected to Hatchet Cloud. Do not mock, stub, or bypass the Hatchet client/server interaction.
- The workflow name on Hatchet must be unique per run by reading the `ZEALT_RUN_ID` environment variable and using the workflow name `linear-dag-${ZEALT_RUN_ID}`. The same suffix must be used so concurrent runs do not collide on Hatchet Cloud.
- Trigger the workflow exactly once and capture the result of `step3_finalize`. Write the captured object as JSON to `/tmp/result.json` so the verifier can inspect the final output.

## Implementation Hints
- Install the `hatchet-sdk` Python package (`pip install hatchet-sdk`).
- Create a Hatchet client instance, then declare a workflow with `hatchet.workflow(name=...)` and three tasks on it via the workflow's `task(...)` decorator. The third task should declare `parents=[step2_transform]`, and the second `parents=[step1_load]`.
- Inside each child task, use `ctx.task_output(<parent_task_object>)` to retrieve the parent's return value at runtime, as documented in the Hatchet DAG guide.
- Start a Hatchet worker (`hatchet.worker(...).start()` or the async equivalent) that registers the workflow, then trigger the workflow with its `run` / `aio_run` method to fire-and-wait for the result. The worker and the trigger can live in the same script (e.g., start the worker in a background process/thread) or in two separate scripts run one after the other.
- After the workflow completes, serialize the final task output dictionary (the one returned by `step3_finalize`) to `/tmp/result.json` using `json.dump` so the verifier can read it.
- Read `ZEALT_RUN_ID` from the environment and build the workflow name as `linear-dag-${ZEALT_RUN_ID}` before declaring the workflow.

## Acceptance Criteria
- Project path: /home/user/myproject
- Result file: /tmp/result.json
- The project must contain at least one Python source file under `/home/user/myproject/` that imports from the `hatchet_sdk` package and defines a workflow with three tasks named `step1_load`, `step2_transform`, and `step3_finalize` (parents declared in that linear order: `step1_load` -> `step2_transform` -> `step3_finalize`). The workflow name registered on Hatchet must be `linear-dag-${ZEALT_RUN_ID}`, where `ZEALT_RUN_ID` is read from the environment.
- After the task is run, `/tmp/result.json` must exist and contain a JSON object whose top-level `final` field is exactly the string `hello world!`.
- The result in `/tmp/result.json` must be produced by an actual Hatchet workflow run (no mocking of the SDK or the server); the agent must use the real `hatchet-sdk` package configured against Hatchet Cloud via `HATCHET_CLIENT_TOKEN`.

