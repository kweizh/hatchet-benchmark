# Hatchet: Per-Key Concurrency Control (Python)

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue with first-class concurrency control. By providing a CEL expression as the concurrency key, you can guarantee that only N task runs share the same key are processed in parallel. A common use-case is to serialize payment processing per `userId` so that no two payments for the same user can run at the same time, while different users can still be processed concurrently.

A local `hatchet-lite` engine and Postgres are already running inside the container. The `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` environment variables are automatically exported (sourced from `/etc/zealt/hatchet.sh` via `BASH_ENV`) so the SDK connects to the local engine without any additional setup.

## Requirements
- Build a Hatchet Python task named `process_payment` that is configured with a per-key concurrency limit of exactly 1 keyed by `userId` so that only one run per user can execute at a time.
- The task input must be a JSON-serializable object with two fields: `userId` (string) and `amount` (integer).
- For every invocation the task MUST:
  - Capture the current Unix time in **milliseconds** at the start of processing.
  - Sleep for at least 2 seconds to simulate work.
  - Capture the current Unix time in milliseconds at the end of processing.
  - Append a single line to a shared log file at `/tmp/payments.log` in the exact format `<userId>:<amount>:<unix_ms_start>:<unix_ms_end>\n`. The write must be performed in a way that is safe under concurrent appends from multiple worker processes (e.g. open with `"a"` mode and rely on the OS append semantics, or use a file lock).
  - Return a JSON-serializable object equal to `{"userId": <userId>, "processed": true}`.
- Provide a runnable worker script that registers the task and starts the Hatchet worker.
- Provide a runnable trigger script that, given `--user-id <userId>` and `--amount <amount>` CLI flags, fires the `process_payment` task, waits for the run to complete, and prints the returned result as a single JSON object on stdout.

## Implementation Hints
- Use the `hatchet-sdk` package (already installed). The Hatchet client picks up the `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_HOST_PORT` environment variables automatically.
- The current Hatchet Python API expresses per-key concurrency via `ConcurrencyExpression` (from `hatchet_sdk`): `ConcurrencyExpression(expression="input.userId", max_runs=1, limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN)`.
- You can attach concurrency either at workflow level (`hatchet.workflow(..., concurrency=ConcurrencyExpression(...))`) or directly on a standalone task (`@hatchet.task(concurrency=ConcurrencyExpression(...))`). Either is acceptable as long as the `userId` keying works.
- The CEL expression operates on the validated input. Use a Pydantic `BaseModel` with a `userId` field so that `input.userId` resolves correctly.
- The Hatchet Python worker uses `multiprocessing` with the `spawn` start method, so the call to `worker.start()` MUST be guarded by `if __name__ == "__main__":`.
- For the start/end timestamps, use `time.time_ns() // 1_000_000` or `int(time.time() * 1000)` to obtain integer milliseconds.
- The trigger script must use the task's fire-and-wait method (e.g. `process_payment.run(...)`) so it does not return until the workflow run finishes.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 trigger.py --user-id <userId> --amount <amount>`
  - It must fire the `process_payment` task with the given input.
  - It must wait for the task to finish.
  - On success, it must print a single JSON object on stdout that matches `{"userId": <userId>, "processed": true}`.
- Log file: `/tmp/payments.log`
  - Each successful task run must append exactly one line in the format `<userId>:<amount>:<unix_ms_start>:<unix_ms_end>` where the two timestamps are integer milliseconds since the Unix epoch and `unix_ms_end - unix_ms_start >= 2000`.
- The task must be registered with a per-key concurrency limit of `1` keyed on the `userId` input field. When two runs are fired for the same `userId`, their execution intervals must not overlap in time. When two runs are fired for different `userId` values, their execution intervals are allowed to overlap.

