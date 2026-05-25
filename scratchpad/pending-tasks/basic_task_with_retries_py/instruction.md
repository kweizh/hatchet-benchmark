# Hatchet Task with Automatic Retries (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine that supports durable execution. Each task can be configured with a `retries` count so that transient failures automatically re-run on a worker without bespoke error-handling code. In this task you will use Hatchet's Python SDK to implement a task that demonstrates this built-in retry mechanism end-to-end against a real Hatchet server.

## Requirements
- Implement a Hatchet **standalone task** in Python that wraps a flaky function which fails on its first two attempts and succeeds on the third.
- The task must be configured to allow **at least 3 retries** so the third attempt can run.
- On every attempt, the task must log the current retry count (read from the Hatchet `Context` object).
- Register a Hatchet worker, trigger the task once, wait for the task to finish, and write the final outcome and per-attempt log lines to a log file.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- A standalone task can be declared with the `@hatchet.task(name=..., retries=...)` decorator. The task function receives an input (e.g. `EmptyModel`) and a `Context` object as positional arguments.
- Use `ctx.retry_count` inside the task body to decide whether to raise an exception. The first call has `retry_count == 0`, the next is `1`, and so on.
- A long-running worker process is required to actually execute the task. Use the SDK worker API to register the task and start the worker (in a background thread or subprocess), then trigger the task with the SDK's run helper and wait for it to complete.
- The task name registered with Hatchet must be unique per concurrent trial. Read `ZEALT_RUN_ID` from the environment and use it as a suffix.
- Once the task has completed, write the per-attempt log lines and the final outcome to the required log file before exiting.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet task name: `flaky-task-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The task is configured with `retries >= 3` so it can be retried at least twice.
- The flaky function raises an exception when `ctx.retry_count < 2` and returns a successful result otherwise.
- The Hatchet task is triggered once against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`) and the worker runs to completion.
- After completion, the log file `/home/user/myproject/output.log` must contain:
  - One line for every attempt in the format: `Attempt retry_count=<N>` where `<N>` is the value of `ctx.retry_count` on that attempt (so the file contains the lines `Attempt retry_count=0`, `Attempt retry_count=1`, and `Attempt retry_count=2`).
  - A final line in the format: `Task succeeded after 3 attempts`.

