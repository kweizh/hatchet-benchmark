# Durable Event Wait with Lookback Window

## Background
Hatchet's durable tasks can pause execution and wait for an external event to arrive using `ctx.aio_wait_for_event`. However, a common race condition occurs when the external event is triggered *before* the task actually begins waiting for it. To solve this, Hatchet provides a lookback window feature that allows the wait condition to consider events that arrived recently.

## Requirements
Write a Python script that defines a Hatchet durable task which waits for a user creation event, but correctly handles the case where the event might have already occurred up to 5 minutes before the wait started.

- Create a file `worker.py` in `/home/user/project`.
- Define a Pydantic model `UserInput` with a `user_id` string field.
- Define a durable task named `ProcessUser` that takes `UserInput`.
- Inside the task, wait for an event with key `user:create`.
- The wait must use a CEL expression to match the `user_id` from the input.
- The wait must use a scope of `user_id:<user_id>`.
- The wait must include a lookback window of 5 minutes to catch events that happened before the wait started.
- The task should return the event payload.

## Constraints
- Project path: /home/user/project
- Use `hatchet-sdk` for Python.
- Use `timedelta` from the `datetime` module for the lookback window.