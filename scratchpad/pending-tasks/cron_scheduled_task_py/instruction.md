# Hatchet: Recurring Cron-Triggered Task

## Background
Hatchet supports cron-style triggers that fire workflow runs on a fixed schedule. By attaching a cron expression to a task/workflow definition, every registered worker will automatically execute the task at the configured cadence — there is no need to manually create a separate schedule. In this exercise you will build a small Python project that defines a task with an attached cron trigger that runs once a minute, against a real, locally running Hatchet server (hatchet-lite + Postgres).

A local Hatchet server is already running inside the container, and the SDK is preconfigured via the `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_TLS_STRATEGY=none`, and `HATCHET_CLIENT_HOST_PORT` environment variables. You can connect to it directly using `hatchet-sdk` from Python.

## Requirements
- Define a single Hatchet workflow/task named `heartbeat` whose task definition declares a cron trigger that fires every minute (cron expression `* * * * *`). The cron must be declared inline on the task/workflow definition (e.g. via the `on_crons=["* * * * *"]` parameter); a programmatically created cron is **not** sufficient.
- Each time the cron trigger fires the task, the task body must append one line to `/tmp/heartbeat.log`. Each line must:
  - Start with the literal prefix `heartbeat ` (note the trailing space).
  - Be followed by an ISO-8601 UTC timestamp produced by Python (for example `2026-05-25T04:31:00.123456+00:00`).
  - End with a single newline.
- Implement a runnable worker script `worker.py` that:
  - Imports and registers the `heartbeat` workflow/task with the local Hatchet engine.
  - Starts a Hatchet worker (`worker.start()`) so the cron trigger can actually execute the task.
  - When invoked as `python worker.py`, the script must block until terminated (i.e. the worker stays running, ready to receive cron-scheduled runs).

## Implementation Hints
- Use the `hatchet-sdk` package (already installed). Initialize the client via `Hatchet(debug=True)` (or the recommended factory) so it picks up the `HATCHET_CLIENT_TOKEN` env var automatically.
- A cron trigger can be attached directly to a workflow definition. The Python helper accepts an iterable of cron expressions, e.g. `hatchet.workflow(name="heartbeat", on_crons=["* * * * *"])` or `@hatchet.task(name="heartbeat", on_crons=["* * * * *"])`. Either pattern is acceptable as long as the cron expression is declared on the task/workflow definition itself.
- The task input can be an empty Pydantic model (e.g. `EmptyModel`) since this task does not require structured input.
- Append to `/tmp/heartbeat.log` using a normal file-write (e.g. `open("/tmp/heartbeat.log", "a")`); be sure to flush the line so the verifier can read it immediately. Generate the timestamp with `datetime.datetime.now(datetime.timezone.utc).isoformat()`.
- Register the workflow/task with the worker the same way you would register a regular task: `worker = hatchet.worker("heartbeat-worker", workflows=[heartbeat]); worker.start()`.
- Cron schedules in Hatchet are UTC and are only attempted while at least one worker is registered for the workflow — `worker.py` must be running for the cron to actually fire.

## Acceptance Criteria
- Project path: /home/user/project
- Log file: /tmp/heartbeat.log
- Worker start command: `python worker.py`
  - The worker must register a task/workflow literally named `heartbeat` whose definition declares the cron expression `* * * * *`.
  - While the worker runs, the cron trigger must fire the task at least once per minute, and each fired run must append exactly one line to `/tmp/heartbeat.log`.
- Each line in `/tmp/heartbeat.log` must match the format `heartbeat <iso8601-utc-timestamp>` followed by a single newline.

