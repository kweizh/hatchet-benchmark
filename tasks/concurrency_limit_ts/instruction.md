# Hatchet TypeScript: Per-Region Concurrency Limit

## Background
You are building an order-processing service on Hatchet Cloud using the TypeScript SDK (`@hatchet-dev/typescript-sdk`). To prevent race conditions in a downstream legacy system that only accepts one in-flight order per geographic region, you must enforce a strict concurrency limit of `maxRuns: 1` keyed by the order's `region` field. Orders from different regions must still be able to run in parallel.

In this task, you will implement a Hatchet task named `processOrder`, register it on a worker, and write a runner that fires 4 parallel runs (2 US, 2 EU) to demonstrate that the concurrency limit is enforced per region while different regions run in parallel.

## Requirements
- Use the `@hatchet-dev/typescript-sdk` package. Do not mock the SDK.
- Implement a Hatchet task named `processOrder` with concurrency configured via a CEL expression on the `region` input field, with `maxRuns: 1`.
- The task body must:
  1. Append a `start <region> <epochMs>` line to the log file.
  2. Sleep approximately 1.5 seconds (1500 ms).
  3. Append an `end <region> <epochMs>` line to the log file.
- Provide a worker entrypoint that registers `processOrder` and starts the worker.
- Provide a runner script that fires 4 runs in parallel using `Promise.all`: 2 with region `US-<run-id>` and 2 with region `EU-<run-id>`, then waits for all of them to complete.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable to namespace the region keys and the log file path. This avoids cross-trial collisions on Hatchet Cloud concurrency keys.
- Authenticate with Hatchet Cloud using `HATCHET_CLIENT_TOKEN` from the environment. Do not hardcode a server URL; rely on the SDK default.

## Implementation Hints
- Use `hatchet.task({ name, concurrency: { ... }, fn: ... })` to declare the task. Refer to the Hatchet TypeScript concurrency documentation for the exact option shape.
- Append to the log file with `fs.appendFileSync` so writes are atomic line-by-line; use `\n` as the line terminator and integer `Date.now()` for the epoch-millis timestamp.
- Use `Promise.all` to submit 4 runs concurrently via `processOrder.run({ region })`.
- The worker must be running before the runner submits jobs; you may start the worker as a background process and the runner as a foreground command.
- Truncate the log file at the start of the runner so the verifier sees a clean state for the current trial.

## Acceptance Criteria
- Project path: /home/user/myproject
- Read `run-id` from the `ZEALT_RUN_ID` environment variable. Use `US-${run-id}` and `EU-${run-id}` as the two region values.
- Log file: `/tmp/orders-${run-id}.log`
- Worker start command: `pnpm run worker` (or equivalent `tsx src/worker.ts`); the worker must register the `processOrder` task and stay running.
- Runner command: `pnpm run runner` (or equivalent `tsx src/runner.ts`); the runner fires 4 runs in parallel and exits once all complete.
- The `processOrder` task must be configured with a concurrency strategy keyed by the `region` input field with `maxRuns: 1`.
- Log line format (one entry per line, exactly three space-separated fields):
  - `start <region> <epochMs>` written immediately when the task starts.
  - `end <region> <epochMs>` written immediately before the task returns.
  - `<region>` is the literal region string from the input (e.g. `US-zr-abc123`).
  - `<epochMs>` is a base-10 integer of milliseconds since Unix epoch.
- After the runner completes, the log file must contain exactly 8 lines: 4 `start` and 4 `end` lines, 2 of each per region.
- Each task run must sleep approximately 1500 ms between its `start` and `end` lines.

