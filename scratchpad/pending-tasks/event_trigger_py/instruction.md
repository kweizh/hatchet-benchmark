# Hatchet Event-Triggered Task (Python)

## Background
Hatchet is a distributed task queue and durable workflow engine. Tasks can be configured to run automatically when an event is pushed to Hatchet, which is useful for fan-out patterns like running multiple independent reactions to a single business event (e.g., `user:created`).

In this task you will build a small Python project that registers an event-triggered Hatchet task, runs a worker, pushes an event, and verifies that the task body was actually executed by checking a file written to disk.

## Requirements
- Use the Hatchet Python SDK (`hatchet-sdk`) targeting Hatchet Cloud. Authentication is provided via the `HATCHET_CLIENT_TOKEN` environment variable; do **not** override the Hatchet server address (the SDK default points at Hatchet Cloud).
- Define a Hatchet task named `on_user_created` that is triggered by the event key `user:created` (i.e., `on_events=["user:created"]`).
- The task body must write a JSON record to the file `/tmp/triggered.json` containing two top-level fields:
  - `event_payload`: the entire input payload that triggered the task (a JSON object including the `user_id` field that was pushed).
  - `received_at`: an ISO 8601 timestamp string for when the task body ran.
- Provide a single runner entrypoint that performs the full end-to-end flow in one process invocation:
  1. Removes any pre-existing `/tmp/triggered.json` file.
  2. Starts the Hatchet worker that has the `on_user_created` task registered (run it in the background so the script can continue).
  3. Waits long enough for the worker to register with Hatchet Cloud.
  4. Pushes an event with key `user:created` and a payload `{"user_id": "abc-<run-id>"}`, where `<run-id>` is read from the `ZEALT_RUN_ID` environment variable.
  5. Waits approximately 10 seconds (and no more than ~60 seconds) for Hatchet to dispatch the event back to the worker and for the task body to write `/tmp/triggered.json`.
  6. Exits cleanly (the worker may be terminated as part of cleanup).
- No mocking: the event must be pushed to the real Hatchet Cloud API and the task must be executed by a real Hatchet worker.

## Implementation Hints
- Read about event-triggered tasks at https://docs.hatchet.run/home/run-on-event. In Python, you can attach an event trigger directly to a task using `@hatchet.task(name=..., on_events=[...])`.
- Create the Hatchet client with `from hatchet_sdk import Hatchet` and instantiate it (e.g., `hatchet = Hatchet()`); it picks up `HATCHET_CLIENT_TOKEN` automatically.
- Build a worker with `hatchet.worker("<name>", workflows=[<task>]).start()` and run it in a background process/thread so the runner script can also push events.
- Push events from the same Python process (or a sibling process) using `hatchet.event.push("user:created", {"user_id": f"abc-{run_id}"})`.
- Read the run id from the `ZEALT_RUN_ID` environment variable before pushing the event.
- Inside the task body, serialize the input back to a plain dict (for example, by calling `.model_dump()` on a Pydantic input model or by accepting a dict-like input) and write the JSON file with the standard library `json` module.

## Acceptance Criteria
- Project path: /home/user/myproject
- Output file: /tmp/triggered.json
- Runner command (executed from `/home/user/myproject`): `python3 run.py`
  - The command starts the worker, pushes the `user:created` event, waits for the task to run, and exits without requiring any further input.
  - The command must exit within 120 seconds.
- The Hatchet task is declared with `on_events=["user:created"]` and named `on_user_created` (the registered Hatchet task name as visible in code).
- After running `python3 run.py`, the file `/tmp/triggered.json` exists and contains a JSON object with the following shape:
  ```json
  {
    "event_payload": { "user_id": "abc-<run-id>", "...": "..." },
    "received_at": "<ISO 8601 timestamp string>"
  }
  ```
  where `<run-id>` is the value of the `ZEALT_RUN_ID` environment variable used during the run.
- `event_payload.user_id` must equal `abc-${ZEALT_RUN_ID}` exactly.
- The environment variable `HATCHET_CLIENT_TOKEN` is required for the worker and the event client to authenticate against Hatchet Cloud.

