# Hatchet Durable Sleep Workflow (Python)

## Background
Hatchet supports *durable* execution: a task can pause for a wall-clock duration without holding a worker slot, and resume exactly once the sleep elapses. This is achieved through the `durable_task` decorator and the `DurableContext` helpers like `aio_sleep_for`. Your job is to implement a small durable task and trigger it to demonstrate this primitive.

## Requirements
- Build a Hatchet worker in Python that registers a single durable task named `delayed_greeter`.
- The task must be defined with `@hatchet.durable_task(name="delayed_greeter")` so the registered name on the Hatchet engine is exactly `delayed_greeter`.
- When invoked, the task should:
  1. Record `start_ts` (the current time in UTC, as integer milliseconds since the epoch).
  2. Durably sleep for 5 seconds using Hatchet's durable sleep API (NOT `time.sleep` or `asyncio.sleep`).
  3. Record `end_ts` (UTC ms after the sleep) and compute `elapsed_ms = end_ts - start_ts`.
  4. Return a dict-like result with the three integer fields `start_ts`, `end_ts`, and `elapsed_ms`.
- Provide a worker entrypoint that registers the task and starts the worker process.
- Provide a trigger entrypoint that, when run, invokes `delayed_greeter` (with an empty input), waits for its completion, and prints the returned JSON object to stdout on a single line in the format `RESULT: {"start_ts": ..., "end_ts": ..., "elapsed_ms": ...}`.

## Implementation Hints
- Hatchet's Python SDK exposes the durable execution APIs via a `DurableContext` (e.g. `from hatchet_sdk import Hatchet, DurableContext, EmptyModel`).
- Use `await ctx.aio_sleep_for(timedelta(seconds=5))` inside an async durable task.
- Use the task object's `aio_run` (or equivalent) method from the trigger script to invoke the task and await its result.
- The Hatchet engine and a Postgres database are already running inside the container; the worker must connect using the `HATCHET_CLIENT_TOKEN` environment variable that is already exported in the container.

## Acceptance Criteria
- Project path: /home/user/myproject
- Worker start command: `python3 /home/user/myproject/worker.py`
- Trigger command: `python3 /home/user/myproject/trigger.py`
- The task must be registered with Hatchet under the exact name `delayed_greeter`.
- Running the trigger command (after the worker is started in the background) must print exactly one line to stdout in the format:
  `RESULT: {"start_ts": <int>, "end_ts": <int>, "elapsed_ms": <int>}`
  where all three values are integers, and `elapsed_ms` is between 5000 (inclusive) and 30000 (exclusive).
- The durable sleep must be performed by Hatchet's durable execution API, not by a process-local sleep.

