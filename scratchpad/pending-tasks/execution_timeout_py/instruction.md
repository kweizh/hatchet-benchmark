# Hatchet Task with Execution Timeout (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine that supports durable execution. Each task can be configured with an `execution_timeout` so that runaway tasks are automatically cancelled and reported as failed once they exceed the configured deadline. In this task you will use Hatchet's Python SDK to implement a task that intentionally exceeds its execution timeout and verify that the Hatchet server cancels it end-to-end against a real Hatchet server.

## Requirements
- Implement a Hatchet **standalone task** in Python whose body sleeps for **10 seconds** (e.g., via `time.sleep(10)` or `asyncio.sleep(10)`).
- Configure the task with an **`execution_timeout` of 3 seconds** (using either `timedelta(seconds=3)` or the string `"3s"`).
- Configure the task with **`retries=0`** so the timeout is observed exactly once with no retry attempts.
- Register a Hatchet worker, trigger the task once, wait for the task to finish (either via success or via the expected failure/cancellation), and record the run-id and start/end timestamps in a log file.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- A standalone task can be declared with the `@hatchet.task(name=..., execution_timeout=..., retries=0)` decorator. The decorator's `execution_timeout` accepts a `datetime.timedelta` or a duration string such as `"3s"`.
- A long-running worker process is required to actually execute the task. Use the SDK worker API to register the task and start the worker (in a background thread or subprocess), then trigger the task with the SDK's run helper and wait for it to complete or fail.
- The task name registered with Hatchet must be unique per concurrent trial. Read `ZEALT_RUN_ID` from the environment and use it as a suffix.
- The triggering code is expected to observe an error/failure from `run` (because the task is cancelled by the server at the 3-second mark). Catch it and treat it as the expected outcome.
- After the run completes (success or failure), write the run-id, the start timestamp, the end timestamp, and the observed final outcome to the required log file before exiting.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet task name: `slow-task-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The task is configured with `execution_timeout` equal to 3 seconds and `retries=0`.
- The task body sleeps for 10 seconds (i.e., would take 10 seconds if not cancelled).
- The Hatchet task is triggered once against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`) and the worker runs until the task finishes (cancelled by the timeout).
- After completion, the log file `/home/user/myproject/output.log` must contain:
  - A line in the format: `Run ID: ${ZEALT_RUN_ID}`
  - A line in the format: `Start: <unix_epoch_seconds>` where `<unix_epoch_seconds>` is a floating-point or integer Unix timestamp recorded immediately before the task is triggered.
  - A line in the format: `End: <unix_epoch_seconds>` where `<unix_epoch_seconds>` is a floating-point or integer Unix timestamp recorded immediately after the task finishes (failure or cancellation).
  - A line in the format: `Outcome: <status>` where `<status>` indicates the observed terminal status (e.g., `FAILED`, `CANCELLED`, or `TIMED_OUT`).

