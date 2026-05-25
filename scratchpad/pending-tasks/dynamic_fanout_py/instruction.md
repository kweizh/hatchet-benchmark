# Dynamic Fan-out with Hatchet Python SDK (Child Spawning)

## Background
You will build a distributed task pipeline using the [Hatchet](https://hatchet.run) Python SDK that demonstrates **dynamic fan-out via child spawning**. A *parent* workflow receives a batch of integers, spawns one *child* workflow per item to perform a computation, then aggregates the results in the original input order.

This pattern is heavily used in real Hatchet applications — for example, when a parent task receives a list of documents at runtime and fans out one OCR/extract job per document. Crucially, the number of children is **not known at workflow-definition time**: it depends on the runtime input.

Hatchet Cloud is already provisioned, and the worker authentication token is provided via the `HATCHET_CLIENT_TOKEN` environment variable. You do NOT need to set a server URL — the Python SDK targets Hatchet Cloud by default.

## Requirements
- Implement two Hatchet workflows using the Python SDK (`hatchet-sdk`):
  1. A **child** workflow named `square_item` that accepts a single integer field `item` and returns `{ "square": item * item }`.
  2. A **parent** workflow named `process_batch` that accepts `{ "items": [int, int, ...] }` (a JSON-serializable list of integers).
- The parent workflow MUST dynamically spawn one `square_item` child workflow per element in the input list (child spawning / fan-out — not hardcoded N children).
- The parent MUST await ALL children and aggregate their `square` outputs into a list, preserving the **original input order** of `items`.
- The parent's final return value MUST be a JSON-serializable object of the form `{ "squares": [<int>, <int>, ...] }`.
- Register both workflows on a Hatchet worker, start the worker, then trigger the parent workflow ONCE with the input `{ "items": [1, 2, 3, 4, 5] }`.
- Wait for the parent run to complete (fire-and-wait), then write its final output to the file `/tmp/result.json` as valid JSON.

## Implementation Hints
- Install the `hatchet-sdk` Python package.
- Authenticate by reading the `HATCHET_CLIENT_TOKEN` environment variable; the SDK picks this up automatically.
- Use Hatchet's child-spawning API to invoke the child workflow from within the parent's task function. In the Python SDK this looks like calling the child workflow's run method (sync `run` or `aio_run`) from inside the parent's task body. The bulk variants (`aio_run_many` / `run_many` with `create_bulk_run_item`) are well suited for fanning out.
- Whichever approach you choose, you MUST preserve original input order in the aggregated `squares` list.
- A Hatchet worker must be running (in the background or another process) when you trigger the parent workflow, otherwise the run will be queued forever.
- Trigger the parent workflow from a separate client script (or after worker startup) — do NOT just call the parent function directly as a plain Python function; the run must go through Hatchet so child spawning actually happens.
- After receiving the parent's result, persist it to `/tmp/result.json` using `json.dump` (UTF-8, standard JSON).

## Acceptance Criteria
- Project path: `/home/user/myproject`
- The `hatchet-sdk` Python package is used (no mocking, no fake in-process replacement of Hatchet).
- A Hatchet worker that registers BOTH `process_batch` (parent) AND `square_item` (child) workflows is started against Hatchet Cloud using the `HATCHET_CLIENT_TOKEN` environment variable.
- The parent workflow `process_batch` is triggered exactly once with input `{ "items": [1, 2, 3, 4, 5] }`, and its final output is written to `/tmp/result.json`.
- `/tmp/result.json` MUST be a JSON file containing an object with a `"squares"` key whose value is a list of integers, in the order corresponding to the original input list.
- The parent workflow's implementation MUST fan out by **spawning child workflow runs at runtime** (one `square_item` child per input item) — it must not compute the squares directly inside the parent task body.

