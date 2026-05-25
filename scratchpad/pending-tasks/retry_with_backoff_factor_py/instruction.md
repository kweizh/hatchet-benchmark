# Hatchet Task with Exponential-Backoff Retries (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine with first-class support for durable execution and retries. In addition to a simple retry count, the Python SDK lets you configure an **exponential backoff** policy for a task using `backoff_factor` (the multiplicative growth factor between successive attempts) and `backoff_max_seconds` (an upper cap on the per-step delay). In this task you will exercise that policy end-to-end against a real Hatchet server, observing the actual wall-clock delays between attempts.

## Requirements
- Implement a Hatchet **standalone task** in Python that wraps a flaky function which fails on its first three attempts and succeeds on the fourth attempt.
- Configure the task with an exponential backoff retry policy using `retries=4`, `backoff_factor=2`, and `backoff_max_seconds=30`.
- On every attempt, the task body must log a single line containing the current retry count and an ISO-8601 UTC timestamp captured *at the start of that attempt*.
- Register a Hatchet worker, trigger the task once against the real Hatchet server, wait for the task to finish, and write the per-attempt log lines and the final outcome to a log file.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- A standalone task can be declared with the `@hatchet.task(name=..., retries=..., backoff_factor=..., backoff_max_seconds=...)` decorator. The task function receives an input model (e.g. `EmptyModel`) and a `Context` object.
- Use `ctx.retry_count` inside the task body to decide whether to raise an exception. The first call has `retry_count == 0`; raise an exception while `retry_count < 3` and return success otherwise.
- A long-running worker process is required to actually execute the task. Use the SDK worker API to register the task and start the worker (e.g. in a background thread), then trigger the task with the SDK's run helper and wait for the run to complete.
- The task name registered with Hatchet must be unique per concurrent trial. Read `ZEALT_RUN_ID` from the environment and use it as a suffix.
- Capture each attempt's start timestamp from inside the task body (e.g. `datetime.now(timezone.utc).isoformat()`) and write one line per attempt to the log file. The verifier will use these timestamps to confirm that the gaps between attempts grow roughly exponentially (gap2 ≈ 2x gap1, gap3 ≈ 2x gap2, within tolerance).
- After the task has completed, write the per-attempt log lines and the final outcome line to the required log file before exiting.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet task name: `backoff-task-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The task is configured with `retries=4`, `backoff_factor=2`, and `backoff_max_seconds=30`.
- The flaky function raises an exception when `ctx.retry_count < 3` and returns a successful result otherwise.
- The Hatchet task is triggered once against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`) and the worker runs to completion.
- After completion, the log file `/home/user/myproject/output.log` MUST contain:
  - Exactly four attempt lines, one per attempt, each on its own line and in the format: `Attempt retry_count=<N> timestamp=<ISO8601_UTC>` where `<N>` is the value of `ctx.retry_count` on that attempt (so `N` takes the values 0, 1, 2, 3 in order) and `<ISO8601_UTC>` is the wall-clock UTC timestamp captured at the start of that attempt.
  - A final outcome line in the format: `Task succeeded after 4 attempts`.

