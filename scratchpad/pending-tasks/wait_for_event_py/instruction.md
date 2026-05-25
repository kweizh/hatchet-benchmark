# Hatchet: Durable Task that Waits for an External Event

## Background
Hatchet supports durable tasks that can pause execution and wait for an external event before continuing. This is the foundation for human-in-the-loop workflows, webhook-driven pipelines, and any process that depends on signals from outside the task. In this exercise you will build a small Python project that defines a durable task waiting for a user-driven event, against a real, locally running Hatchet server (hatchet-lite + Postgres).

A local Hatchet server is already running inside the container, and the SDK is preconfigured via the `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_TLS_STRATEGY=none`, and `HATCHET_CLIENT_HOST_PORT` environment variables. You can connect to it directly using `hatchet-sdk` from Python.

## Requirements
- Define a single Hatchet **durable** task named `onboarding` using `@hatchet.durable_task(name="onboarding")`.
- The task must pause until a `user:profile_completed` event is received via the durable event-wait helper on the durable context (the up-to-date Python helper is `await ctx.aio_wait_for_event("user:profile_completed")`).
- Once the event arrives, the task must return a JSON-serializable mapping shaped like `{"status": "completed", "payload": <event_payload>}` where `<event_payload>` is the dict that was pushed alongside the event.
- Implement a runnable worker script `worker.py` that registers the durable task with the local Hatchet engine.
- Implement a runnable trigger script `trigger.py` that:
  1. Fires the `onboarding` task (fire-and-forget; capture the run reference).
  2. Waits a short moment to let the task subscribe to the event wait.
  3. Pushes the `user:profile_completed` event via the Hatchet event client (`hatchet.event.push("user:profile_completed", {...})`) with payload `{"userId": "u1"}`.
  4. Waits for the workflow run to complete and prints the final result as a single JSON object on stdout.

## Implementation Hints
- Use the `hatchet-sdk` package (already installed). Initialize the client via `Hatchet(debug=True)` (or the recommended factory) so it picks up the `HATCHET_CLIENT_TOKEN` env var automatically.
- A durable task is declared with `@hatchet.durable_task(...)` and its function receives a `DurableContext` whose `aio_wait_for_event(event_key)` method establishes a durable event wait. The return value of `aio_wait_for_event` exposes the event payload (look for the `.data` attribute on the returned object, or use whatever accessor the SDK provides).
- Register the durable task with the worker the same way you would register a regular task: `worker = hatchet.worker("<worker-name>", workflows=[onboarding]); worker.start()`.
- To trigger the durable task without blocking, use `onboarding.run_no_wait(...)` (or the equivalent async API), then call `.result()` / `.aio_result()` on the returned run reference to wait for completion.
- To push the event from the trigger, use `hatchet.event.push("user:profile_completed", {"userId": "u1"})`.
- The task input can be an empty Pydantic model (e.g. `EmptyModel`) since this task does not require structured input.
- Print exactly one JSON object on the trigger script's stdout (no extra prefix lines) so the verifier can parse it.

## Acceptance Criteria
- Project path: /home/user/project
- Worker start command: `python worker.py`
- Trigger command: `python trigger.py`
  - It must trigger the `onboarding` durable task, push a `user:profile_completed` event with payload `{"userId": "u1"}`, wait for the run to finish, and print the final result.
  - On success, the last non-empty stdout line must be a JSON object that satisfies:
    - `status` equals the string `"completed"`.
    - `payload` equals the JSON object `{"userId": "u1"}`.
- The task must be registered with the literal name `onboarding` and declared via `@hatchet.durable_task`.

