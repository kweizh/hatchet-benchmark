# Hatchet Programmatic Cron-Scheduled Task (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine that supports recurring task execution via cron triggers. In addition to declaring `on_crons` statically on a workflow definition, the Python SDK exposes a REST-backed `cron` feature client that lets you programmatically create, list, and delete cron schedules at runtime. In this task you will use Hatchet's Python SDK to register a task on a real Hatchet server, create a per-minute cron schedule for it programmatically, and confirm that the cron successfully triggers at least one run.

## Requirements
- Implement a Hatchet **standalone task** in Python that, when invoked, appends the current UTC ISO-8601 timestamp to a log file.
- Register a Hatchet worker for the task and start it so the cron-triggered runs can actually execute.
- After the worker is up, **programmatically** create a cron schedule for the task using the Hatchet Python SDK's `cron` feature client (or the equivalent `Standalone.create_cron(...)` convenience method) with the expression `* * * * *` (every minute).
- Append a single line to the log file recording the cron name and the cron creation acknowledgement (i.e. the id returned by the SDK).
- Keep the worker running long enough for the cron to fire at least once, then exit. The whole task script should not run for more than ~90 seconds.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- A standalone task can be declared with the `@hatchet.task(name=...)` decorator. The Python SDK reads `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` from the environment automatically when you construct `Hatchet()`.
- Programmatic cron creation in the Python SDK is exposed in two equivalent ways:
  - On the standalone/workflow object: `my_task.create_cron(cron_name=..., expression="* * * * *", input=<input model>, additional_metadata={...})`.
  - On the client's `cron` feature client: `hatchet.cron.create(workflow_name=..., cron_name=..., expression=..., input=..., additional_metadata=...)`.
  Either approach returns a `CronWorkflows` object whose `metadata.id` is the cron trigger id.
- A long-running worker process is required to actually execute the task. Start the worker (for example, in a background thread) so the cron-triggered runs can be picked up, then sleep for long enough (~70 seconds) for at least one cron tick to occur, then exit.
- The task name and the cron schedule name must be unique per concurrent trial. Read `ZEALT_RUN_ID` from the environment and use it as a suffix.
- Before exiting, the log file should record the cron name and the cron creation acknowledgement (the id of the created cron trigger) on a single line.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet task name: `heartbeat-task-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- Hatchet cron name: `heartbeat-cron-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- Cron expression: `* * * * *` (every minute).
- The cron schedule is created programmatically via the Hatchet Python SDK against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`).
- After the task script exits, the log file `/home/user/myproject/output.log` must contain a single acknowledgement line in the format: `Created cron heartbeat-cron-${ZEALT_RUN_ID} id=<cron_trigger_id>` where `<cron_trigger_id>` is the id returned by the SDK when the cron was created.

