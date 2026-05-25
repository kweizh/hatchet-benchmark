# Dynamic Fan-out with Child Task Spawning (Hatchet Python SDK)

## Background
Hatchet is a distributed task queue and durable workflow engine. One of its most powerful primitives is **child spawning**: a parent task can dynamically spawn child tasks at runtime, allowing fan-out over lists of unknown length. In this task, you must implement a parent workflow that receives a list of integers, fans out one child per integer to compute its square, awaits the results, and aggregates them into a sum.

A real Hatchet server is reachable through the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`. You must connect to that real server — do NOT mock the Hatchet client or any of its primitives.

## Requirements
- Implement a Python project at `/home/user/myproject` that uses the `hatchet-sdk` package.
- Define a **child task** that accepts a single integer input and returns its square.
- Define a **parent task** that accepts an input shaped like `{"items": [int, ...]}` and, at runtime, spawns one child task per item using Hatchet's child-spawning API (e.g., `await child.aio_run(...)` invoked once per item from within the parent, gathered concurrently).
- The parent task must wait for all child results and return an output shaped like `{"total": <int>}` where `total` is the sum of the squared values.
- Start a worker that registers both the parent and the child tasks, trigger the parent with the input list `[1, 2, 3, 4, 5]`, wait for the run to complete, and record the result.

## Implementation Hints
- Use the Hatchet Python SDK (`hatchet-sdk`, installed via pip3). Refer to the [Child Spawning](https://docs.hatchet.run/v1/child-spawning) and [Tasks](https://docs.hatchet.run/v1/tasks) documentation.
- Read connection info from `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the SDK reads these automatically when set).
- Workflow/task names registered against the server **MUST** be suffixed with `${ZEALT_RUN_ID}` (read from the `ZEALT_RUN_ID` environment variable) to avoid collisions across parallel runs.
- Spawn children concurrently from within the parent (e.g., gather coroutines such as `asyncio.gather(*[child.aio_run(...) for item in items])`) so the workflow truly fans out rather than running children serially.
- Use `asyncio` and async tasks throughout. A single worker registering both parent and child is sufficient.
- After triggering the parent and obtaining the result, write the run information to a log file.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- Hatchet task names must be registered as:
  - Parent task name: `fanout-parent-${ZEALT_RUN_ID}`
  - Child task name: `fanout-child-${ZEALT_RUN_ID}`
  where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The parent task must take an input of the shape `{"items": [int, ...]}` and return an output of the shape `{"total": <int>}` where `total` equals the sum of the squares of the items.
- The child task must take a single integer input and return that integer squared.
- A worker must be started (registering both the parent and the child against the real Hatchet server) and the parent must be triggered with the input `{"items": [1, 2, 3, 4, 5]}`.
- After the run completes successfully, the log file `/home/user/myproject/output.log` must contain at least the following two lines, in this exact format:
  - `Run ID: <workflow_run_id>`
  - `Total: <total>`
  where `<workflow_run_id>` is the Hatchet workflow run ID returned by the SDK when triggering the parent, and `<total>` is the integer total returned by the parent task (which must equal `55` for the input `[1, 2, 3, 4, 5]`).
- Children must actually be spawned through Hatchet's child-spawning mechanism (i.e., the child task must be registered separately and invoked from within the parent's function body), not by computing the squares inline inside the parent.

