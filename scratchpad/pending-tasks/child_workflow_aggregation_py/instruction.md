# Child Workflow Aggregation with Hatchet (Python)

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue and workflow engine. One of its core features is the ability to spawn and await child workflows from within a parent task at runtime, enabling map-reduce style pipelines. In this task you will build a parent workflow that orchestrates a word-count map-reduce by spawning a dedicated child workflow per input string and aggregating the results.

A local `hatchet-lite` engine plus PostgreSQL are already running inside the container. `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY=none` are already exported in the environment (they are sourced automatically from `/etc/zealt/hatchet.sh` via `BASH_ENV`).

## Requirements
- Define a **standalone child workflow** named `count_words`. It must be declared as a Hatchet workflow object (i.e. via `hatchet.workflow(...)` plus an attached task) and **not** as a bare `@hatchet.task(...)`. It takes an input with a single string field `text` and returns an output with two fields:
  - `count`: the number of whitespace-separated words in `text`.
  - `words`: the list of whitespace-separated tokens of `text` (in original order).
- Define a **parent workflow** named `aggregate_word_counts`. It takes an input with a single list field `texts` (a list of strings). In its main task, it must spawn one run of the `count_words` child workflow per element of `texts` using the Hatchet child-workflow spawn API, await all of their results, and return an output object with two fields:
  - `total`: the sum of all child `count` values.
  - `per_text`: the list of child `count` values, in the **same order** as the input `texts`.
- Both workflows must be registered on the **same** worker process, so a single worker entrypoint can serve all runs.
- Provide a worker entrypoint script (`worker.py`) that registers both workflows and starts the Hatchet worker.
- Provide a trigger script (`run.py`) that accepts the input strings as command-line arguments, runs the `aggregate_word_counts` parent workflow with `{"texts": [<args>]}`, waits for completion, and prints the result.

## Implementation Hints
- Use the official `hatchet-sdk` Python package (already installed). Import the global Hatchet client with `from hatchet_sdk import Hatchet` and instantiate it once at module top-level.
- Declare the child as a workflow object (e.g. `count_words = hatchet.workflow(name="count_words", ...)` with a `count_words.task(...)` attached) so that it is a proper standalone workflow, not just a single task.
- A child workflow can be invoked from within a parent task by calling `await child.aio_run(input, ...)`, or in bulk via `await child.aio_run_many([child.create_bulk_run_item(input=...) ...])`. See https://docs.hatchet.run/v1/child-spawning for details.
- Use Pydantic `BaseModel` classes for the input and output schemas (e.g. `class CountWordsInput(BaseModel): text: str`).
- The Hatchet Python worker uses `multiprocessing` with the `spawn` start method, so the call to `worker.start()` MUST be guarded by `if __name__ == "__main__":` or it will fail with a bootstrap error.
- The parent's `per_text` output MUST be ordered the same way as the input `texts` list (i.e. the i-th element of `per_text` is the count for `texts[i]`).
- The trigger script should print the aggregated result on its own two dedicated lines using exactly this format:
  - `Total: <int>`
  - `PerText: [<n1>, <n2>, ...]` (standard Python list repr with spaces after commas)

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py`
- Trigger command: `python3 run.py <text1> <text2> ...` (each text passed as a single shell argument; use quoting for multi-word strings)
- The worker process must register a standalone child workflow named `count_words` that takes input `{"text": <str>}` and returns output containing `{"count": <int>, "words": [<str>, ...]}` where `count` equals `len(text.split())` and `words` equals `text.split()`.
- The worker process must also register a parent workflow named `aggregate_word_counts` that takes input `{"texts": [<str>, ...]}` and returns output containing `{"total": <int>, "per_text": [<int>, ...]}` where `total` is the sum of per-element counts and `per_text` preserves the input order.
- When the worker is running, executing the trigger script with any list of inputs must:
  - exit with status `0`,
  - print a line matching exactly `Total: <int>` (the sum of per-element counts), and
  - print a line matching exactly `PerText: [<n1>, <n2>, ...]` (the per-element counts in input order).
- The parent workflow MUST spawn the per-text counts via the Hatchet child-workflow spawn API (e.g. `count_words.aio_run(...)`, `count_words.aio_run_many(...)`, `count_words.run(...)`, or `spawn_workflow("count_words", ...)`); it MUST NOT compute the counts locally inside the parent task body.

