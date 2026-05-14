# Wait for Event or Timeout

## Background
Create a Hatchet workflow that simulates an order processing system. It needs to wait for a user confirmation event for up to 5 minutes before automatically cancelling the order.

## Requirements
- Define a Hatchet workflow named `OrderWorkflow` with a durable task `process_order`.
- The task must use `ctx.aio_wait_for` to wait for either a `UserEventCondition` with `event_key="user:confirm"` or a `SleepCondition` of 5 minutes.
- If the event is received, the task should return `{"status": "confirmed"}`.
- If the timeout occurs, the task should return `{"status": "cancelled"}`.

## Constraints
- Project path: `/home/user/myproject`
- The worker must be runnable via `python worker.py`.

## Integrations
- Hatchet