# Hatchet Global (Static) Rate Limit Workflow (Python SDK)

## Background
Hatchet's **static rate limits** (formerly called "global" rate limits) allow you to throttle task executions against shared resources whose capacity is known in advance, such as the request limits of an external API. A rate limit key is declared once via the admin client, and any task that opts into the key by declaring `rate_limits=[RateLimit(static_key=...)]` is throttled against the shared bucket. In this task you will use Hatchet's Python SDK to implement a task that respects a global rate limit and observe Hatchet throttling 6 parallel runs against a 3-per-minute budget on a real Hatchet server.

## Requirements
- Use the Hatchet Python SDK to declare a **static rate limit** before the worker starts (limit = 3, duration = `MINUTE`).
- Implement a Hatchet **standalone task** whose definition includes `rate_limits=[RateLimit(static_key=..., units=1)]` referencing that key.
- The task body must append a single record to a shared log file containing the wall-clock start timestamp of the run and the run id (read from `ctx.workflow_run_id` or an equivalent identifier exposed by `Context`).
- Trigger the task **6 times in parallel** against the same Hatchet server, then wait until every triggered run completes successfully.
- After all 6 runs finish, write a `Done` marker line to the same log file so the verifier can confirm completion.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).
- The rate-limit key and the task name MUST be suffixed with `${ZEALT_RUN_ID}` so concurrent trials do not collide.

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- Declare the static rate limit with `hatchet.rate_limits.put(key, limit, RateLimitDuration.MINUTE)` before starting the worker.
- Attach the limit to a task by passing `rate_limits=[RateLimit(static_key=key, units=1)]` to `@hatchet.task(...)`.
- A long-running worker is required to actually execute tasks. Start the worker in a background thread or subprocess so the same script can submit work to it.
- Use the SDK's bulk-run or run-no-wait helpers (e.g. `task.run_many_no_wait(...)` or 6 calls to `task.aio_run_no_wait(...)` from `asyncio.gather`) to trigger 6 runs nearly simultaneously, then poll/await each handle until it finishes successfully.
- Each task invocation should append a single line of the form `ts=<epoch_seconds_float> run_id=<workflow_run_id>` to the log file using `open(path, "a")` so timestamps are preserved even when runs are throttled.
- After every run has reported success, write the literal line `Done` to the log file.
- Read `ZEALT_RUN_ID` from the environment once and reuse the same value for the rate-limit key suffix and the task name suffix.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet static rate limit key: `openai-api-${ZEALT_RUN_ID}` (limit = 3, duration = `MINUTE`).
- Hatchet task name: `rate-limited-task-${ZEALT_RUN_ID}`.
- The task definition attaches the static rate limit via `rate_limits=[RateLimit(static_key="openai-api-${ZEALT_RUN_ID}", units=1)]`.
- The task is triggered 6 times in parallel against the real Hatchet server using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`. All 6 runs must complete with a successful status.
- After every run completes, the log file `/home/user/myproject/output.log` must contain:
  - Exactly 6 lines (in any order) of the form: `ts=<epoch_seconds_float> run_id=<workflow_run_id>`, one per executed run, where `<epoch_seconds_float>` is the wall-clock start time of that run (a positive float) and `<workflow_run_id>` is a non-empty string.
  - A final line containing the literal text `Done`.
- The 6 recorded timestamps, when sorted ascending, demonstrate Hatchet's rate limiter throttling the bucket of 3 per minute:
  - The first 3 timestamps are within 10 seconds of each other.
  - The 4th timestamp occurs at least 30 seconds after the 1st timestamp (i.e. the 4th run waited for the next rate-limit window).

