# Hatchet Python Durable Sleep Task

## Background
Hatchet is a distributed task queue and workflow engine that provides durable execution semantics. One of its hallmark features is *durable sleep*: a task can pause for a specified duration without holding worker resources, and the wait is guaranteed across worker restarts and replays.

You will build a small Python project that defines a Hatchet **durable task** that sleeps for ~5 seconds using Hatchet's durable sleep API, then returns a structured result. A runner script triggers the task synchronously and writes the result to a fixed JSON file on disk.

## Requirements
- Implement a Hatchet durable task named `delayed_greeting` that:
  - Captures the wall-clock start time at the very beginning of the task.
  - Sleeps durably for approximately 5 seconds using Hatchet's durable sleep API (NOT Python's `time.sleep` and NOT `asyncio.sleep` alone).
  - After waking, computes `elapsed_sec` as the integer number of wall-clock seconds between the start time and the end of the task.
  - Returns a JSON-serializable result of the shape `{"message": "wakeup", "elapsed_sec": <int>}` where `elapsed_sec >= 5`.
- Implement a runner that:
  - Starts a Hatchet worker that registers the `delayed_greeting` durable task.
  - Triggers the task and waits for it to complete (synchronously, end-to-end).
  - Writes the final task result (the dict above) as JSON to `/tmp/result.json`.
  - Exits cleanly with status code 0 after writing the file.
- Use the **Hatchet Cloud** managed service. Do NOT run a local Hatchet engine. Authenticate with the real `HATCHET_CLIENT_TOKEN` value provided in the environment.
- Do NOT mock the Hatchet SDK, the worker, or the cloud service. The result must come from a real round-trip through Hatchet Cloud.

## Implementation Hints
- Install the `hatchet-sdk` Python package.
- Construct a `Hatchet` client (it will read `HATCHET_CLIENT_TOKEN` from the environment automatically).
- Define the durable task using the `@hatchet.durable_task(...)` decorator. The handler receives a `DurableContext`.
- Inside the handler, use `await ctx.aio_sleep_for(timedelta(seconds=5))` (or the equivalent sync `ctx.sleep_for(...)`) to perform durable sleep. A plain `time.sleep` or `asyncio.sleep` does not satisfy the task.
- Use the task's `.run(...)` (or `.aio_run(...)`) helper, or trigger via the client and poll for completion. The runner must block until a real result is available, then serialize it to `/tmp/result.json`.
- Start a worker (e.g. `hatchet.worker(name=..., slots=...)` with `worker.start()`) in the same process or a background thread so the task can actually execute.
- Reference docs: https://docs.hatchet.run/llms/v1/durable-sleep.md and https://docs.hatchet.run/llms/v1/durable-tasks.md

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /tmp/result.json
- The runner must be executable as: `python3 /home/user/myproject/run.py`
- After the runner exits with status 0, the file `/tmp/result.json` must exist and contain a JSON object with exactly these properties:
  - `message`: the string `"wakeup"`
  - `elapsed_sec`: an integer greater than or equal to `5`
- The task implementation must use Hatchet's durable sleep API (`@hatchet.durable_task` plus `ctx.aio_sleep_for` or `ctx.sleep_for`).
- Authentication must use the real `HATCHET_CLIENT_TOKEN` environment variable; the Hatchet Cloud default server address is used (no override).

