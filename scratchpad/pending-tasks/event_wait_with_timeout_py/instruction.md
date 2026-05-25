# Hatchet Durable Event Wait with Timeout (Python)

## Background
Hatchet's durable execution allows a task to pause until an external event arrives or a timeout expires. This pattern is the foundation for human-in-the-loop flows, webhook-driven pipelines, and "wait-or-give-up" deadlines. You will implement a durable Python task that combines an event wait and a sleep using Hatchet's `Or(...)` grouping so that the task proceeds whichever condition fires first.

## Requirements
- Use the Python SDK (`hatchet-sdk`) installed via `pip3` to define and run a Hatchet durable task.
- The durable task must wait for **either** a user event with key `user:profile-completed:${ZEALT_RUN_ID}` **or** a 30 second sleep timeout, whichever happens first.
- Connect to a real Hatchet server using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` from the environment.
- Trigger one run of the workflow as a one-off job, wait for completion, and write the run result to a log file.

## Implementation Hints
- Read `run-id` from the `ZEALT_RUN_ID` environment variable and use it to suffix the workflow name (e.g., `wait-flow-${run-id}`) and the event key (`user:profile-completed:${run-id}`).
- Use Hatchet's `@hatchet.durable_task(...)` decorator to define a durable task and accept the durable context.
- Inside the durable task, log the line `Waiting for user-profile-completed event or 30 second timeout` to stdout (or via the worker logger).
- Use `ctx.aio_wait_for(Or(UserEventCondition(event_key=...), SleepCondition(duration=timedelta(seconds=30))))` (or the equivalent durable wait helper) to wait for either signal. The Hatchet Python SDK exposes these symbols from `hatchet_sdk` (e.g., `Or`, `UserEventCondition`, `SleepCondition`).
- After the wait returns, decide whether an event was received or the wait timed out. Return a dict shaped `{"received_event": <bool>, "payload": <dict or null>}`.
- Use a single Python entry script that: starts a worker in the background (or in a separate process/thread), triggers exactly one run of the workflow, waits for the run to finish, then writes the final result to the log file and exits. The verifier will push the event, so do **not** push the event from your task script.
- Use the worker's `start()`/`async_start()` API and the workflow client's `run` / `aio_run` (or `run_no_wait` + poll) helpers to obtain the run result.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The workflow MUST be named exactly `wait-flow-${ZEALT_RUN_ID}` (with `${ZEALT_RUN_ID}` substituted from the environment variable).
- The durable task MUST wait for an event with key exactly `user:profile-completed:${ZEALT_RUN_ID}` OR for a 30 second sleep, whichever occurs first.
- The first time the durable task runs, it MUST emit the exact log line: `Waiting for user-profile-completed event or 30 second timeout`.
- After completion, the log file MUST contain exactly one line in the format: `Run result: <json>` where `<json>` is a single-line JSON object with keys `received_event` (boolean) and `payload` (object or null).
- When the verifier pushes the event `user:profile-completed:${ZEALT_RUN_ID}` with payload `{"userId": "test"}` shortly after the workflow starts, the result JSON MUST have `received_event: true` and `payload` MUST include `"userId": "test"`.
- The task command MUST run as a single one-off invocation (e.g., `python3 /home/user/myproject/main.py`) that exits after the run completes.

