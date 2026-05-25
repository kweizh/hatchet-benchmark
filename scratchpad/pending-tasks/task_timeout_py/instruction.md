# Hatchet: Task with Execution Timeout

## Background
Hatchet is a distributed task queue with durable execution. Each task can declare an execution timeout that bounds how long the task is allowed to run after it has been picked up by a worker. When the timeout is exceeded, Hatchet cancels the task and the run is marked as failed (not as a successful completion). In this exercise you will build a small Python project that demonstrates Hatchet's execution-timeout enforcement against a real, locally running Hatchet server (hatchet-lite + Postgres).

A local Hatchet server is already running inside the container and the SDK is preconfigured via the `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_TLS_STRATEGY` environment variables. You can connect to it directly using `hatchet-sdk` from Python.

## Requirements
- Define a single Hatchet task named `slow_task` configured with `execution_timeout="3s"` using the Hatchet Python SDK (e.g. `@hatchet.task(name="slow_task", execution_timeout="3s")`).
- The task body must call `time.sleep(10)` and, if it ever gets past the sleep, return `{"ok": true}`. The expectation is that the sleep never completes because the execution timeout fires first.
- Implement a runnable worker script that registers the task with the local Hatchet engine.
- Implement a runnable trigger script that fires the `slow_task` task, waits for the run to finish, and reports the final outcome on stdout as a single JSON object.
  - On success path (which should NOT happen under correct configuration), the trigger script must print `{"status": "succeeded", "output": <task_output>}`.
  - On the expected failure path (timeout), it must catch the failure and print `{"status": "failed", "error": "<error_message_from_hatchet>"}` where `<error_message_from_hatchet>` is the error string Hatchet reports for the failed run.

## Implementation Hints
- Use the `hatchet-sdk` package (already installed). Initialize the client via `Hatchet(debug=True)` (or the recommended factory) so it picks up the `HATCHET_CLIENT_TOKEN` env var automatically.
- The `execution_timeout` parameter accepts a duration string like `"3s"` (or a `datetime.timedelta`). Refer to the official Hatchet timeouts documentation if needed.
- Use `hatchet.worker("<worker-name>", workflows=[slow_task])` and `worker.start()` to run the worker.
- In the trigger script, fire the task (e.g. `slow_task.run()` or `aio_run()`) and wrap the wait in a try/except so a Hatchet failure raises an exception you can capture and re-emit as JSON.
- Print exactly one JSON object on the trigger script's stdout (no extra prefix lines) so the verifier can parse it.

## Acceptance Criteria
- Project path: /home/user/project
- Worker start command: `python worker.py`
- Trigger command: `python trigger.py`
  - It must trigger the `slow_task` task with no input (or an empty input model).
  - It must wait for the task to finish (success or failure).
  - It must print a single JSON object on stdout that, under correct configuration, has:
    ```json
    {"status": "failed", "error": "<string mentioning timeout or cancellation>"}
    ```
  - The `error` string must be non-empty and must contain a substring that signals a timeout / cancellation (one of: `TIMED_OUT`, `timeout`, `timed out`, `cancel`, case-insensitive).
- The task must be registered with the literal name `slow_task` and an execution timeout of 3 seconds.

