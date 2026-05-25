# Hatchet Bulk Fan-out and Aggregation (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine designed for durable execution. For high-throughput scenarios where many invocations of the same task must be triggered together, Hatchet provides bulk-trigger APIs that send all invocations to the server in a single network round trip, then resolve a list of results when every run finishes.

In this task, you will build a small Python program that defines a Hatchet task, starts a worker, and uses Hatchet's **bulk run API** to fan out 20 invocations in parallel, await all their results, and aggregate them into a final sum.

## Requirements
- Use the `hatchet-sdk` Python SDK and connect to a real Hatchet server using the credentials provided via environment variables.
- Define a single Hatchet task named `process-item-${run-id}` (where `run-id` comes from the `ZEALT_RUN_ID` environment variable) that:
  - Takes a Pydantic input containing a single integer field `value`.
  - Returns a result containing `result = value * 2 + 1`.
- Register the task on a Hatchet worker and start the worker so it can pick up runs.
- From the same Python process (the "driver"), use Hatchet's **bulk run** API to trigger 20 runs of the task at once with inputs `[{"value": 0}, {"value": 1}, ..., {"value": 19}]` and await all results in a single bulk call (not 20 individual `run`/`aio_run` calls).
- Sum the `result` values from all 20 outputs and write a single summary line to the log file in the exact format `Total sum: <sum>` (e.g. `Total sum: 420`).
- The program must run as a one-off job: start the worker, run the bulk trigger, write the log line, and exit cleanly (non-zero exit code on failure).

## Implementation Hints
- Read `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` from the environment to authenticate the Hatchet client. The SDK reads these automatically when constructing `Hatchet()`.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable and embed it in the task name so concurrent runs do not collide.
- Look at the Hatchet docs on "Running Tasks in Bulk" for the Python bulk API. The relevant SDK helpers are `Workflow.create_bulk_run_item(...)` together with `Workflow.aio_run_many(...)` (or its blocking counterpart `run_many`).
- Because the worker and the bulk trigger live in the same process, you will need to run the worker in the background (for example, on a separate thread or asyncio task) so the main driver can issue the bulk call and await results.
- Make sure all 20 runs complete successfully before computing the sum; do not write `Total sum:` if any run failed.
- Use `hatchet-sdk` installed via `pip3`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The Hatchet task name registered on the worker MUST be `process-item-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- Exactly 20 successful runs of that task must exist on the Hatchet server after the program exits.
- The 20 inputs must be `value = 0, 1, 2, ..., 19` (one input per run, in any order).
- The 20 invocations must be triggered using Hatchet's bulk-trigger Python API (`run_many` / `aio_run_many`), not 20 separate `run`/`aio_run` calls.
- The log file `/home/user/myproject/output.log` must contain a line in the exact format `Total sum: <sum>`, where `<sum>` is the integer sum of the `result` fields returned by all 20 runs.
- The program must exit with code 0 on success.

