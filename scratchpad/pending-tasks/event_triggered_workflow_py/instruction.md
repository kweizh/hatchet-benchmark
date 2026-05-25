# Hatchet Event-Triggered Workflow (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine. In addition to invoking tasks directly, a Hatchet task can be declared to fire **automatically** whenever a matching event is pushed to the Hatchet server. In this task you will implement and run an event-triggered Hatchet worker in Python that listens for a `user:signup` style event and processes the event payload.

The Hatchet server is already reachable; authentication is provided via the `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` environment variables. Do **NOT** mock the Hatchet server.

## Requirements
- Implement a single Hatchet task in Python that is triggered by an event key (use the `on_events` parameter of the task decorator).
- The task must read the event payload, extract an `email` field, and append a welcome line to a log file.
- Start a Hatchet worker that registers the task.
- After the worker is running, push a single event with a known payload using the Hatchet Python SDK.
- The worker may exit cleanly after handling the event; the log file must persist on disk.

## Implementation Hints
- Install and use the `hatchet-sdk` Python package.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable and use it to make the workflow/task name and the event key unique per run.
- Use the `@hatchet.task(name=..., on_events=[...])` decorator pattern. The task receives the event payload as its input; access fields via the input object.
- Use `hatchet.event.push(<event_key>, <payload_dict>)` from the Python SDK to publish the event.
- Start the worker with `worker.start()`; you can run the worker in a background thread/process from the same script, then push the event, then wait until the log file is written, then stop the worker.
- All work must happen inside the project directory.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/welcome.log
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- The Hatchet task must be registered with:
  - name `user-signup-handler-${run-id}`
  - `on_events` containing the event key `user:signup:${run-id}`
- After the task completes, the log file must contain a line in the format: `Welcomed user <email>`
- The event must be pushed using the Hatchet Python SDK with event key `user:signup:${run-id}` and a JSON payload that includes an `email` field.
- The workflow run must be visible in the Hatchet server's run list and must have been triggered by the matching event key (verifiable via the Hatchet SDK / runs API).

