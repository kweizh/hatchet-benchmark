# Hatchet Durable Sleep Workflow (Python)

## Background
Hatchet is a distributed task queue and workflow engine that supports **durable execution**. One of its core durable primitives is the ability for a task to **sleep durably**: the task pauses for a specified amount of time without holding worker resources, and the wait is guaranteed to respect the original duration even across worker restarts, evictions, or crashes.

Your job is to build a Python program that defines a Hatchet **durable task** which sleeps for 5 seconds using the durable-sleep API, then triggers the task against a real Hatchet server, waits for the run to complete, and logs the elapsed time.

## Requirements
- Use the `hatchet-sdk` Python package.
- Connect to a real Hatchet server using the `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` environment variables. Do NOT mock Hatchet.
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable and use it to build a unique workflow name `durable-sleep-${run-id}` so concurrent runs do not collide.
- Define a durable task with `@hatchet.durable_task` whose body:
  - records a start timestamp,
  - calls the durable sleep primitive on the durable context to sleep for **5 seconds**,
  - records an end timestamp,
  - returns a JSON-serializable object containing `start_ts`, `end_ts`, and `duration_sec` (a float computed as `end_ts - start_ts`).
- Provide a runnable script that:
  - registers the durable task on a worker,
  - starts the worker in the background,
  - triggers the workflow once,
  - waits for the workflow run to finish,
  - writes the run ID and the final output to a log file.

## Implementation Hints
- Look at the Hatchet Python SDK durable-task and durable-sleep APIs (`@hatchet.durable_task`, `DurableContext`, and `aio_sleep_for` / `sleep_for`).
- The durable context exposes an async sleep helper that takes a `datetime.timedelta`.
- You will likely want a single Python entrypoint that both starts a worker (in a background thread or subprocess) and triggers the workflow, so the whole task can run as a one-off job inside the container.
- Use the workflow client (e.g. `workflow.run(...)` or `workflow.aio_run(...)`) to trigger the durable task and obtain its output once it completes.
- After the run completes, print/append the run id and the result to the log file in the exact formats listed in Acceptance Criteria.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The Hatchet workflow / durable task must be registered with the name `durable-sleep-${run-id}`, where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The durable task must use Hatchet's durable-sleep primitive (e.g. `ctx.aio_sleep_for(timedelta(seconds=5))` or the sync equivalent) to wait for 5 seconds; it must NOT use a plain language-level sleep such as `time.sleep` or `asyncio.sleep` for the durable wait.
- The Python program must connect to a real Hatchet server using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`.
- After triggering and awaiting the workflow, the log file must contain:
  - A line in the format: `Run ID: <workflow_run_id>`
  - A line in the format: `Output: <json_output>` where `<json_output>` is a JSON object containing the numeric fields `start_ts`, `end_ts`, and `duration_sec`.
  - The reported `duration_sec` must be at least 5.0 (proving the durable sleep actually waited).

