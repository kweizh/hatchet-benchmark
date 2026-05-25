# Hatchet Scheduled Run (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine that supports durable execution. One of its core features is the ability to programmatically schedule a one-time future run of a registered task. In this task you will use the Hatchet Python SDK (`hatchet-sdk`) to define a task, schedule it to run once in the near future, run a worker to pick up that scheduled execution, and finally clean up the schedule.

## Requirements
- Implement a Hatchet task named `scheduled-hello` in Python that, when fired, writes a JSON object of the form `{"fired_at": "<iso8601 utc timestamp>", "input": <input dict>}` to `/tmp/scheduled_result.json`.
- Programmatically schedule the task to run ONE TIME at approximately `now + 15 seconds` (UTC) with input `{"name": "world"}` using the Hatchet Python SDK's scheduled-run API.
- Start a Hatchet worker that has the task registered so the scheduled run can be picked up and executed.
- Wait long enough (at least ~30 seconds total) for the scheduled time to pass and for the task to actually execute on the worker.
- After execution, delete (clean up) the scheduled run via the SDK so no stale schedule is left behind.
- The task must connect to Hatchet Cloud using the credentials provided through the `HATCHET_CLIENT_TOKEN` environment variable. Do not hard-code tokens or mock the Hatchet service.

## Implementation Hints
- Install and use the `hatchet-sdk` Python package.
- A Hatchet client is created with `Hatchet()` (it reads `HATCHET_CLIENT_TOKEN` from the environment; no server URL configuration is needed for Hatchet Cloud).
- Tasks are defined with the `@hatchet.task(...)` decorator. Inside the task body you receive the input and can write to a file on disk.
- Use the task object's `schedule(...)` method to programmatically create a one-off future run, passing a UTC `datetime` (e.g. `datetime.now(tz=timezone.utc) + timedelta(seconds=15)`) and an `input=` dict.
- A worker must be running on the same client to actually execute the scheduled task. Run the worker in the background (e.g. a thread or subprocess) so your main script can also wait and then delete the schedule.
- Use `hatchet.scheduled.delete(scheduled_id=<schedule.metadata.id>)` (or the equivalent attribute exposed by the SDK) to remove the scheduled run during cleanup.
- The whole orchestration (define task + schedule + run worker + wait + cleanup) should live in one or a few Python files under the project directory.
- Use `ZEALT_RUN_ID` from the environment only if you also write additional log artifacts; the primary output file path `/tmp/scheduled_result.json` is fixed by the requirements.

## Acceptance Criteria
- Project path: /home/user/myproject
- The task uses the real Hatchet Cloud service authenticated via the `HATCHET_CLIENT_TOKEN` environment variable.
- After the orchestration finishes, the file `/tmp/scheduled_result.json` must exist and contain a JSON object with:
  - A field `input` whose value is an object containing `"name": "world"`.
  - A field `fired_at` whose value is a valid ISO 8601 timestamp string (parseable by `datetime.fromisoformat`, accepting a trailing `Z` as UTC).
- The scheduled run must have been created via the Hatchet Python SDK's scheduled-run API (not via CLI or dashboard).
- The scheduled run is deleted via the SDK after it fires (cleanup step is executed).

