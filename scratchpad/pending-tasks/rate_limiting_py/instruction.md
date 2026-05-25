# Hatchet: Static Rate Limiting for External API Calls (Python)

## Background
[Hatchet](https://docs.hatchet.run) supports static (global) rate limiting on task runs through its [rate limits API](https://docs.hatchet.run/v1/rate-limits). Static rate limits are declared up front via the rate-limits client and consumed by tasks via the `rate_limits` configuration on the task definition. When a task run would exceed the declared limit, Hatchet automatically holds the run until the rate-limit window admits it. This is the canonical way to throttle calls to an external API that enforces a strict global request budget across all tenants.

A local `hatchet-lite` engine and Postgres are already running inside the container. The `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` environment variables are automatically exported (sourced from `/etc/zealt/hatchet.sh` via `BASH_ENV`) so the SDK connects to the local engine without any additional setup.

## Requirements
- Build a Hatchet Python task named `external_api_call` whose runs are governed by a **static** (global) rate limit of **3 requests per minute**.
- The rate limit key must be exactly `external_api`. Each task run consumes `1` unit of that key.
- The static rate limit must be declared from the worker process before the worker starts accepting runs (using the Hatchet rate-limits client, e.g. `hatchet.rate_limits.put("external_api", 3, RateLimitDuration.MINUTE)`).
- For every invocation the task MUST:
  - Capture the current Unix time in **milliseconds**.
  - Append a single line to `/tmp/rate.log` containing only the integer millisecond timestamp followed by a newline (e.g. `1716620000123\n`). The write must be safe under concurrent appends from multiple worker processes (use append mode and rely on OS append semantics, or use a file lock).
  - Return a JSON-serializable object equal to `{"ok": true}`.
- Provide a runnable worker script (`worker.py`) that:
  - Declares the static rate limit `external_api` with a budget of 3 units per minute.
  - Registers the `external_api_call` task with the static rate-limit consumption configured via `rate_limits=[RateLimit(static_key="external_api", units=1)]`.
  - Starts the Hatchet worker.
- Provide a runnable trigger script (`trigger.py`) that fires the `external_api_call` task once, waits for the run to complete, and prints the returned result as a single JSON object on stdout in the exact format `{"ok": true}`.

## Implementation Hints
- Use the `hatchet-sdk` package (already installed). The Hatchet client picks up the `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_HOST_PORT` environment variables automatically.
- The static rate limit is declared with the rate-limits client: `hatchet.rate_limits.put(KEY, limit, duration)`. The consumption is declared on the task with `rate_limits=[RateLimit(static_key=KEY, units=1)]` (import `RateLimit` and `RateLimitDuration` from `hatchet_sdk`).
- The supported `RateLimitDuration` values are fixed enum members (`SECOND`, `MINUTE`, `HOUR`, ...). Use `RateLimitDuration.MINUTE` for this task.
- A 1-minute window with budget 3 means the first 3 concurrent runs are admitted immediately; subsequent runs only get admitted once the window has refilled.
- The Hatchet Python worker uses `multiprocessing` with the `spawn` start method, so the call to `worker.start()` MUST be guarded by `if __name__ == "__main__":`. The `hatchet.rate_limits.put(...)` call should run on worker startup (before `worker.start()`).
- For the timestamp, use `time.time_ns() // 1_000_000` or `int(time.time() * 1000)` to obtain integer milliseconds.
- The Hatchet Python SDK returns the task output as an `EmptyModel`-style Pydantic object when no `input_validator` / output type is configured. The trigger script must convert the SDK return value to a `dict` (e.g. via `dict(result)`, `result.model_dump()`, or by directly constructing `{"ok": True}` after the run completes successfully) before passing it to `json.dumps`, so that stdout always contains the canonical JSON object `{"ok": true}`.
- The trigger script must use the task's fire-and-wait method (e.g. `external_api_call.run({})`) so it does not return until the workflow run finishes.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 trigger.py`
  - It must fire the `external_api_call` task with an empty input.
  - It must wait for the task to finish.
  - On success, it must print a single JSON object on stdout equal to `{"ok": true}` (i.e. `json.loads(stdout_last_line) == {"ok": True}`).
- Log file: `/tmp/rate.log`
  - Each successful task run must append exactly one line containing an integer millisecond timestamp.
- The static rate limit must be registered with the Hatchet engine under the key `external_api` with `limit_value == 3` and `window == '1 MINUTE'` (queryable via the Hatchet rate-limits API, e.g. `hatchet.rate_limits.list()`).
- The task must consume the `external_api` static rate limit with `units=1` per run. After 3 task runs within a single window, the `external_api` rate limit must drop to `value == 0` (the budget is exhausted). After waiting one window (>=60s without firing additional runs), the rate limit must refill back to `value == 3` and subsequent runs must succeed.

