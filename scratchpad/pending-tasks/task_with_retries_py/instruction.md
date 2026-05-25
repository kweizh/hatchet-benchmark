# Hatchet: Task with Automatic Retries

## Background
Hatchet is a distributed task queue with durable execution. When a task raises an exception, Hatchet can automatically retry it according to the configured retry policy. In this exercise you will build a small Python project that demonstrates Hatchet's task-level retry behavior against a real, locally running Hatchet server (hatchet-lite + Postgres).

A local Hatchet server is already running inside the container and the SDK is preconfigured via the `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_TLS_STRATEGY` environment variables. You can connect to it directly using `hatchet-sdk` from Python.

## Requirements
- Define a single Hatchet task named `flaky` configured with `retries=3` using the Hatchet Python SDK (`@hatchet.task(name="flaky", retries=3)`).
- The task input must include a counter file path. Reading the counter file path from the input on every attempt is required.
- On each invocation, the task must:
  - Read the integer counter from the file path (treat a missing file as counter `0`).
  - Increment the counter and persist it on disk before deciding whether to fail.
  - Raise an exception when the persisted counter is less than `3`.
  - When the persisted counter equals `3`, return `{"attempt": 3, "succeeded": true}`.
- Implement a runnable worker script that registers the task with the local Hatchet engine.
- Implement a runnable trigger script that fires the `flaky` task with the counter file path provided as a CLI argument, waits for the run to finish, and prints the result as a single JSON object on stdout.

## Implementation Hints
- Use the `hatchet-sdk` package (already installed). Initialize the client via `Hatchet(debug=True)` (or the recommended factory) so it picks up the `HATCHET_CLIENT_TOKEN` env var automatically.
- Use `hatchet.worker("<worker-name>", workflows=[flaky])` and `worker.start()` to run the worker.
- Use fire-and-wait (`flaky.run(...)`) or fire-and-forget plus `result()` to trigger and obtain the output from the trigger script.
- The task input is JSON-serializable. A Pydantic `BaseModel` (e.g. with a single `counter_file` string field) works well.
- The disk write must happen BEFORE the exception is raised so the counter is durably advanced across retries.
- Print exactly one JSON object on the trigger script's stdout (no extra prefix lines) so the verifier can parse it.

## Acceptance Criteria
- Project path: /home/user/project
- Worker start command: `python worker.py`
- Trigger command: `python trigger.py <counter_file_path>`
  - It must trigger the `flaky` task with the given counter file path as input.
  - It must wait for the task to finish.
  - On success, it must print a single JSON object on stdout that matches:
    ```json
    {"attempt": 3, "succeeded": true}
    ```
- After a successful trigger, the counter file at `<counter_file_path>` must contain the integer `3` (the count of attempts the task executed, i.e. initial attempt + 2 retries).
- The task must be registered with the literal name `flaky` and `retries=3`.

