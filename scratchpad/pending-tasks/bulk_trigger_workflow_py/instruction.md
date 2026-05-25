# Bulk-Trigger a Hatchet Task in Python

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue and workflow engine. When you need to enqueue many runs of the same task at once, the Python SDK exposes the bulk-run API (`workflow.run_many(...)` / `aio_run_many(...)`) which avoids the per-call gRPC overhead of triggering each run individually. A local `hatchet-lite` engine and PostgreSQL are already running inside the container, and `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` are pre-exported into every shell via `BASH_ENV`. The `hatchet-sdk` Python package is already installed.

Your job is to (a) define a small `index` task on a worker and (b) write a separate trigger script that uses the SDK's **bulk-run** API to fire 25 runs of that task in a single call, wait for all of them to finish, and print the results.

## Requirements
- In `worker.py`, register a Hatchet task named `index` that:
  - Accepts an input shaped like `{"i": <int>}`.
  - Returns an output shaped like `{"squared": <int>}` where the value equals `i * i`.
  - Uses a Pydantic `BaseModel` for input validation.
- The same `worker.py` must, when run as `python3 worker.py`, register `index` on a worker named `bulk-index-worker` and start the worker process so that the task is available for execution.
- In a separate `bulk.py`, use the Hatchet **bulk-run** API on the `index` task (e.g. `index.run_many(...)` or the async `index.aio_run_many(...)`) to trigger **exactly 25** runs in one call with inputs `i = 0, 1, 2, ..., 24`. Wait for all 25 results, then print them on stdout as a single JSON array of objects, sorted ascending by `i`. Each element must be a JSON object with exactly two fields: `i` (the input integer) and `squared` (the integer returned by the task).
- The JSON array must be printed on its own line of stdout prefixed by `Results:` (a literal label followed by a single space and then the JSON array, e.g. `Results: [{"i": 0, "squared": 0}, ...]`).
- `bulk.py` must NOT call `index.run(...)` 25 times in a Python loop; it MUST use one of the bulk-run entry points (`run_many`, `aio_run_many`, `run_many_no_wait`, or `aio_run_many_no_wait`). If you use a `_no_wait` variant, you must subsequently wait for all run results and then print them in the required format.

## Implementation Hints
- The `Workflow` / standalone `Task` objects returned by `@hatchet.task(...)` expose `.create_bulk_run_item(input=...)` to construct each item, and `.run_many([...])` / `.aio_run_many([...])` to trigger them in bulk. See https://docs.hatchet.run/home/bulk-run for the canonical Python example.
- The Hatchet client picks up `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_HOST_PORT` from the environment automatically when you instantiate `Hatchet()`.
- Each bulk-run result is the task's return value (a `dict` or a Pydantic model). When building the JSON array, normalize each result back into a plain dict (e.g. via `model_dump()`).
- Because the Hatchet Python worker uses `multiprocessing` with the `spawn` start method, guard the `worker.start()` call inside `worker.py` with `if __name__ == "__main__":`.
- `bulk.py` is invoked as a top-level Python script. If you use the async API, wrap it with `asyncio.run(...)`.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 bulk.py`
- `worker.py` registers a task named `index` (optionally namespace-prefixed) on a worker named `bulk-index-worker`. The task accepts `{"i": <int>}` and returns `{"squared": <int>}` with `squared == i * i`.
- `bulk.py` triggers exactly 25 runs of `index` using the Hatchet bulk-run API in a single call (one of `run_many`, `aio_run_many`, `run_many_no_wait`, or `aio_run_many_no_wait`).
- When the worker is running and `python3 bulk.py` is executed, the script must exit with status code `0` and print a line of the exact form `Results: <json>` to stdout, where `<json>` is a JSON array of 25 objects sorted ascending by `i`, and each object has exactly the keys `i` and `squared` with `squared == i * i` for `i` in `0..24`.

