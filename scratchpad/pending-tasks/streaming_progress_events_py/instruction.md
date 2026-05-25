# Hatchet Streaming Progress Events (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine that supports durable execution. In addition to durable input/output, Hatchet tasks can push real-time stream events from a worker back to a consumer using the `Context.put_stream` / `Context.aio_put_stream` API. These events are consumed by subscribing to the workflow run's stream via `hatchet.runs.subscribe_to_stream(workflow_run_id)`. This is commonly used for sending progress updates from long-running tasks or for streaming LLM tokens back to a frontend.

In this task you will implement a Hatchet task that emits progress events for a counted loop, run it on a worker, subscribe to its stream, and persist every received event to a local log file. The task must be executed against a real Hatchet server (no mocks).

## Requirements
- Implement a Hatchet **standalone task** in Python named `count_progress` that accepts an input with a single integer field `n`.
- Inside the task, loop from `1` through `n` (inclusive). For each iteration `i`, push a stream event whose content is the exact string `progress: i/n` (with `i` and `n` substituted) via `ctx.put_stream(...)` or `ctx.aio_put_stream(...)`.
- After the loop completes, the task should return a successful result (e.g. `{"done": true}`).
- Register a Hatchet worker that hosts the task, trigger the task once with `n = 5` (without waiting for the result inline), and subscribe to the resulting workflow run's stream.
- For every chunk received from `hatchet.runs.subscribe_to_stream(...)`, append a single line containing that chunk to a log file. Each chunk must be written on its own line, in the order received.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- A standalone task can be declared with the `@hatchet.task(name=..., input_validator=...)` decorator. The task function receives an input model and a `Context` object as positional arguments.
- To stream progress, use `ctx.put_stream("...")` from a sync task or `await ctx.aio_put_stream("...")` from an async task.
- To consume the stream, first fire-and-forget the task (e.g. `ref = await my_task.aio_run_no_wait(input)` or the sync equivalent), then iterate `hatchet.runs.subscribe_to_stream(ref.workflow_run_id)` (use the async iterator from an async context).
- Per Hatchet's documentation, the consumer must start subscribing before publishing begins. A short sleep at the top of the task (e.g. `await asyncio.sleep(2)`) avoids dropped events.
- A long-running worker process is required to actually execute the task. Use the SDK worker API to register the task and start the worker (in a background thread or subprocess), then trigger the task and consume the stream in the main process.
- The task name registered with Hatchet must be unique per concurrent trial. Read `ZEALT_RUN_ID` from the environment and use it as a suffix (e.g. `progress-counter-${ZEALT_RUN_ID}`).
- After the stream completes and the run reaches a terminal state, exit cleanly. The log file must contain the stream events in the order they were received.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/stream.log`
- Hatchet task name: `progress-counter-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The task is triggered exactly once against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`) with input `n = 5` and runs to completion.
- The task emits 5 stream events of the form `progress: <i>/5` for `i` in `1..5`.
- After completion, the log file `/home/user/myproject/stream.log` must contain, in this exact order (one event per line), the five lines:
  - `progress: 1/5`
  - `progress: 2/5`
  - `progress: 3/5`
  - `progress: 4/5`
  - `progress: 5/5`
- The Hatchet workflow run for `progress-counter-${ZEALT_RUN_ID}` reaches a terminal `SUCCEEDED` status on the Hatchet server.

