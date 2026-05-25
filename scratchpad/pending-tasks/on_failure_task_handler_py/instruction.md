# Hatchet On-Failure Task Handler (Python)

## Background
Hatchet workflows support lifecycle hooks. The `@workflow.on_failure_task()` decorator registers a special task that runs as the last step of a workflow whenever at least one task in the workflow fails. This is useful for cleanup, alerting, or compensating actions.

In this task, you will build a tiny Hatchet workflow whose primary task always fails, and you will attach an on-failure handler that records a cleanup line containing the workflow run id. Your one-off script must trigger the workflow against a real Hatchet server and write the run id into a log file so the result can be verified.

## Requirements
- Create a Python project that uses the `hatchet-sdk` package.
- Define a Hatchet workflow that has:
  - One regular task that always raises an exception (so the workflow always fails).
  - One on-failure task (registered via `@workflow.on_failure_task()`) that writes a cleanup line containing the failed workflow's run id to the shared log file.
- Start a Hatchet worker in the background (in the same script or a sibling process) so the workflow and its on-failure task can actually execute on the real Hatchet server.
- Trigger exactly one run of the workflow from the same script, wait until the run has finished, and record the workflow run id to the log file.
- The script must exit cleanly (exit code 0) once the run has finished and the on-failure handler has had a chance to write its cleanup line.

## Implementation Hints
- Read `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` from the environment; the `Hatchet()` client uses these to connect.
- Read `ZEALT_RUN_ID` from the environment and use it as a suffix in the workflow name (e.g. `failing-flow-${ZEALT_RUN_ID}`) so concurrent trials do not collide.
- The on-failure task receives the same workflow input and a `Context`; the workflow run id is available on the context (for example via `ctx.workflow_run_id`). Write the cleanup line using that id.
- To run the worker and the trigger in one script, start the worker in a background thread (or async task) and trigger the workflow once the worker is up. After the run finishes, stop the worker so the script can exit.
- Use `run_no_wait` / `aio_run_no_wait` to get a `WorkflowRunRef` (which exposes the workflow run id) before awaiting the result, so you can log the same run id that the on-failure task sees.
- The triggered run is expected to end in a failed state; do not let the resulting exception crash your script before the on-failure handler has run. Catch it and continue so the script exits 0.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The script must read `HATCHET_CLIENT_TOKEN`, `HATCHET_SERVER_URL`, and `ZEALT_RUN_ID` from the environment.
- The workflow name registered with Hatchet must be `failing-flow-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is the value of the `ZEALT_RUN_ID` environment variable.
- The workflow must contain at least one regular task that always raises an exception and one on-failure task registered via `@workflow.on_failure_task()`.
- The on-failure task must write a line to the log file in the exact format: `Cleanup ran for run_id=<workflow_run_id>` where `<workflow_run_id>` is the id of the failed workflow run.
- The triggering script must also write a line to the same log file in the exact format: `Triggered run_id=<workflow_run_id>` for the run it triggered.
- After the script finishes, the Hatchet server must report the triggered workflow run with status `FAILED` (any case-insensitive form such as `FAILED` or `failed` is acceptable).
- The script must exit with code 0.

