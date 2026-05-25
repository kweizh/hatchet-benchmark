# Hatchet Per-Key Concurrency Limit (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine. One of its most powerful scheduling features is **per-key concurrency control**, where the platform serializes task runs that share the same key (e.g. the same user_id) while letting unrelated keys continue to execute in parallel. This is the canonical pattern for guaranteeing that no more than one payment for the same user can be processed simultaneously without blocking other users.

In this task you will use Hatchet's Python SDK to implement a concurrency-aware standalone task and run it against a real Hatchet server. Your code must demonstrate true per-key serialization end-to-end: the Hatchet engine (not your code) must be the entity that enforces ordering for runs that share the same key.

## Requirements
- Implement a Hatchet **standalone task** in Python that is configured with a per-key concurrency strategy keyed on `input.user_id`, `max_runs=1`, and the `GROUP_ROUND_ROBIN` limit strategy.
- The task input is a Pydantic model with two fields: `user_id: str` and `op_id: int`.
- Inside the task body, the function must:
  - Record a high-resolution start timestamp (seconds since Unix epoch as a float).
  - Sleep for at least 2 seconds.
  - Record an end timestamp and append a single JSON line to a shared timeline log file under a process-safe filesystem lock (so concurrent workers do not corrupt the file).
  - Return an output object containing `user_id`, `op_id`, `start_ts`, and `end_ts`.
- Register and start a Hatchet worker with enough slots to run all four triggered runs in parallel (so any serialization observed in the timeline must come from Hatchet's concurrency strategy, not from worker slot limits).
- Trigger four runs in parallel against the real Hatchet server:
  - `{user_id: "alice", op_id: 1}`
  - `{user_id: "alice", op_id: 2}`
  - `{user_id: "bob",   op_id: 1}`
  - `{user_id: "bob",   op_id: 2}`
- Wait for all four runs to finish and record both their workflow run IDs and their `(start_ts, end_ts)` intervals in the project log.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- The relevant SDK symbols are `Hatchet`, `Context`, `ConcurrencyExpression`, and `ConcurrencyLimitStrategy` from `hatchet_sdk`.
- A standalone task with per-key concurrency is declared as `@hatchet.task(name=..., input_validator=MyInput, concurrency=ConcurrencyExpression(expression="input.user_id", max_runs=1, limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN))`.
- The task name registered with Hatchet must be unique per concurrent trial: read `ZEALT_RUN_ID` from the environment and use it as a suffix.
- Bulk-trigger the four runs without waiting individually so that the engine can decide ordering. The Python SDK exposes `aio_run_many` (or `run_many`) on the standalone task object together with `create_bulk_run_item` for typed inputs; alternatively, use `aio_run`/`run` with `wait_for_result=False` to enqueue each run and then await the resulting `WorkflowRunRef.aio_result()` / `result()` for each one.
- Start the worker in a background thread so the same process can both trigger the runs and execute them. Make sure the worker is fully connected before triggering, and stop it cleanly afterwards.
- Use `multiprocessing.Lock` or `fcntl.flock` (or another OS-level lock) when appending JSON lines to the shared timeline file so that interleaved workers do not corrupt the log.
- Float seconds (e.g. from `time.time()`) work well as the start/end timestamps. Be sure the start timestamp is captured **before** the 2-second sleep and the end timestamp **after** it.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Project log file: `/home/user/myproject/output.log`
- Per-run timeline file: `/home/user/myproject/timeline.jsonl`
- Hatchet task name: `payment-task-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The Hatchet task is configured with a per-key concurrency limit keyed on `input.user_id`, `max_runs=1`, and the `GROUP_ROUND_ROBIN` strategy.
- The task input schema has at least the two fields `user_id: str` and `op_id: int`.
- The task body sleeps for at least 2 seconds between its start and end timestamps.
- The task is triggered exactly 4 times against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`): two runs with `user_id="alice"` (`op_id` 1 and 2) and two runs with `user_id="bob"` (`op_id` 1 and 2).
- After all 4 runs complete, the timeline file `/home/user/myproject/timeline.jsonl` must contain exactly 4 JSON-Lines records, each with at least the keys `user_id`, `op_id`, `start_ts`, and `end_ts` (numeric epoch seconds).
- After all 4 runs complete, the log file `/home/user/myproject/output.log` must contain:
  - One line per run in the format: `Run user_id=<user_id> op_id=<op_id> run_id=<workflow_run_id>` so the verifier can map each run to its Hatchet workflow run ID.
  - A final summary line in the format: `All 4 runs completed`.

