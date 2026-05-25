# Hatchet TypeScript Cron Heartbeat

## Background
Hatchet is a distributed task queue and workflow engine that supports cron-style scheduled tasks. In this task you will create a small TypeScript program that defines a Hatchet task, registers a cron trigger programmatically against Hatchet Cloud, runs a worker that processes the trigger, and then cleans up the cron registration.

## Requirements
- Define a Hatchet task named `heartbeatTs` using the `@hatchet-dev/typescript-sdk`. Each invocation must append a single line containing the current UTC ISO 8601 timestamp (e.g. `2026-05-25T12:00:00.000Z`) followed by a newline to `/tmp/heartbeats.log`.
- Programmatically create a cron trigger with the name `hb-cron-ts-${ZEALT_RUN_ID}` and the expression `* * * * *` (every minute), passing an empty input object `{}`.
- Start a Hatchet worker so that the task actually executes when the cron fires.
- Keep the worker running for approximately 75 seconds so that at least one cron tick is processed.
- After the run window completes, delete the cron trigger using the SDK's crons delete API and then exit cleanly.

## Implementation Hints
- Use the `@hatchet-dev/typescript-sdk` package. Authenticate by relying on the `HATCHET_CLIENT_TOKEN` environment variable. Do not hard-code or override the Hatchet Cloud server address.
- Run TypeScript directly with `tsx` (already installed in the environment) instead of compiling first.
- Read the `ZEALT_RUN_ID` environment variable and build the cron name as `hb-cron-ts-${ZEALT_RUN_ID}` so that concurrent runs do not collide.
- The Hatchet TS SDK exposes a `.cron(name, expression, input)` method on standalone task objects and a `hatchet.crons.delete(cronId)` method for cleanup. Capture the returned cron's `metadata.id` so you can delete it later.
- Be careful not to block the worker thread; start the worker first (do not `await` its lifetime indefinitely) and then wait ~75 seconds before shutting down and deleting the cron.
- Append to `/tmp/heartbeats.log` using Node's `fs` module. Use `new Date().toISOString()` to produce the ISO timestamp.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /tmp/heartbeats.log
- The project must depend on `@hatchet-dev/typescript-sdk`.
- After the agent finishes executing the task, `/tmp/heartbeats.log` must exist and contain at least one line whose content is a valid ISO 8601 UTC timestamp (format `YYYY-MM-DDTHH:MM:SS(.sss)Z`).
- The cron trigger named `hb-cron-ts-${ZEALT_RUN_ID}` (where `ZEALT_RUN_ID` is taken from the environment) must NOT be present in the Hatchet Cloud cron list after the agent finishes (it must be deleted as cleanup).

