# Linear 3-Step DAG with Hatchet (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine focused on durable execution. A DAG (Directed Acyclic Graph) workflow lets you declare a set of tasks and the dependencies between them; Hatchet automatically schedules tasks in the right order and passes outputs from parent tasks to child tasks through the context object.

In this task you will use the Hatchet **Python SDK** (`hatchet-sdk`) to build a 3-step linear DAG that transforms a `name` input through a chain of three steps and produces a final greeting string. You will then register the workflow on a worker, trigger the workflow with a sample input, wait for it to finish, and write its workflow run ID to a log file.

## Requirements
- Use the `hatchet-sdk` Python package to connect to a real Hatchet server.
- Build a single workflow whose name is exactly `greeting-pipeline-${ZEALT_RUN_ID}`, where `${ZEALT_RUN_ID}` is read from the environment variable `ZEALT_RUN_ID` at runtime.
- The workflow input has a single field `name: str` and must contain three tasks executed sequentially:
  - `step1`: takes the workflow input and returns a JSON-serializable output with a `greeting` field equal to `"Hello " + name` (e.g., for `name="world"` it returns `{"greeting": "Hello world"}`).
  - `step2`: has `step1` as its only parent, reads `step1`'s output via the context (`ctx.task_output(step1)`), and returns an output with a `shouted` field equal to the uppercase version of the greeting (e.g., `{"shouted": "HELLO WORLD"}`).
  - `step3`: has `step2` as its only parent, reads `step2`'s output via the context, and returns an output with a `final` field equal to the shouted string with `"!!!"` appended (e.g., `{"final": "HELLO WORLD!!!"}`).
- Register the workflow on a Hatchet worker and start the worker so that Hatchet can dispatch tasks to it.
- From the same project, trigger the workflow once with the input `{"name": "world"}`, wait for it to finish, and write its workflow run ID to the log file in the exact format `Workflow Run ID: <run_id>`.

## Implementation Hints
- Install the Python SDK with `pip3 install hatchet-sdk`.
- The Hatchet client reads `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` from the environment automatically; both are pre-set in the task environment.
- Create a workflow with `hatchet.workflow(name=...)` and attach tasks with the `@workflow.task(...)` decorator. Use the `parents=[...]` argument to declare dependencies, and call `ctx.task_output(parent_task)` inside child tasks to read parent outputs.
- You can use Pydantic models (e.g., a `BaseModel` with a `name: str` field) for input validation, or just return plain Python dictionaries from each task.
- To execute the DAG end-to-end in one process, start the worker in a background thread (e.g., using Python's `threading` module) and then trigger the workflow from the main thread using the workflow's `run` or `aio_run` method, which blocks until the run completes and returns the result.
- After the run completes, obtain the workflow run ID from the returned reference / context and append the line `Workflow Run ID: <run_id>` to `/home/user/myproject/output.log`.
- Read `ZEALT_RUN_ID` once at startup and reuse the same value when constructing the workflow name and when triggering the run.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The Hatchet workflow name must be `greeting-pipeline-${ZEALT_RUN_ID}` where `ZEALT_RUN_ID` is read from the environment variable.
- The workflow has exactly 3 tasks composed as a linear DAG: `step1 -> step2 -> step3`, using `parents=[...]` and `ctx.task_output(...)` for data flow.
- After running, the log file must contain a line in the exact format `Workflow Run ID: <run_id>` where `<run_id>` is the workflow run ID returned by Hatchet for the triggered run.
- When the workflow is triggered with `{"name": "world"}`, the final task (`step3`) output must contain the field `final` with value `HELLO WORLD!!!`.

