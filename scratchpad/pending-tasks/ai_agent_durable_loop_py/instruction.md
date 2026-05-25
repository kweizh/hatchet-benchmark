# Hatchet Durable AI Agent Loop (Python)

## Background
One of Hatchet's flagship use cases is orchestrating **AI agent loops**: long-running, multi-turn conversations with an LLM where the agent must be able to durably pause between turns, survive worker restarts, and resume exactly once with the same conversation state. In this task you will build such an agent loop using Hatchet's `durable_task` decorator and the `DurableContext` durable-sleep API.

A tiny *mock LLM* HTTP server is already running inside the container at `http://localhost:9100`. It exposes a single `POST /chat` endpoint that accepts a list of chat messages and replies with `{"reply": "<turn-index>: " + last_user_message}`, where `<turn-index>` starts at 1 and increments each time the endpoint is called. On its 3rd response, the server appends ` [DONE]` to the reply, signaling the agent loop to stop. The mock server is a stand-in for a real LLM API — Hatchet itself is **not** mocked.

## Requirements
- Build a Hatchet worker in Python that registers a single durable task named `agent_loop`.
- The task **MUST** be declared with `@hatchet.durable_task(name="agent_loop")` so its registered name on the engine is exactly `agent_loop`.
- The task accepts an input object with two fields:
  - `messages`: a list of chat messages, each shaped as `{"role": str, "content": str}`.
  - `max_turns`: an integer upper bound on the number of assistant turns.
- When invoked the durable task **MUST**:
  1. Record `start_ts` (UTC milliseconds since the epoch).
  2. Loop up to `max_turns` times. In each iteration:
     - `POST` the **current** `messages` list to `http://localhost:9100/chat` as JSON under the key `messages`.
     - Parse the JSON response, extract the `reply` string, and append `{"role": "assistant", "content": <reply>}` to `messages`.
     - If the reply contains the literal substring `[DONE]`, break out of the loop after appending that final assistant message.
     - Otherwise, durably pause for **1 second** using Hatchet's durable sleep API (`await ctx.aio_sleep_for(timedelta(seconds=1))`). Do **NOT** use `time.sleep` or `asyncio.sleep` for this pause.
  3. Record `end_ts` (UTC ms) and compute `elapsed_ms = end_ts - start_ts`.
  4. Return a JSON object with the fields `messages` (the full final conversation history), `turns` (the number of assistant messages added), `start_ts`, `end_ts`, and `elapsed_ms`.
- Provide a worker entrypoint at `/home/user/myproject/worker.py` that registers the task and starts the Hatchet worker.
- Provide a trigger entrypoint at `/home/user/myproject/trigger.py` that invokes the task with input `{"messages": [{"role": "user", "content": "hi"}], "max_turns": 3}`, waits for the run to finish, and prints the returned JSON object to stdout on a single line in the format `RESULT: <json>`.

## Implementation Hints
- Hatchet's Python SDK exposes the durable execution API through a `DurableContext` object (e.g. `from hatchet_sdk import Hatchet, DurableContext`).
- Use Pydantic input/output models or plain dicts via `EmptyModel`-style inputs as you see fit; the engine accepts JSON-serialisable inputs.
- Use any HTTP client (e.g. `requests`, `httpx`) to call the mock LLM. The mock LLM is **not** durable — it is just a normal HTTP dependency.
- The mock LLM keeps a per-process counter on disk, so its `[DONE]` signal is deterministic across restarts of the agent (it fires on the 3rd call regardless of how many times the durable task is replayed).
- The Hatchet engine and a Postgres database are already running inside the container. Use the `HATCHET_CLIENT_TOKEN` environment variable that is exported in the container shell.
- From the trigger script, use the task object's async run API (e.g. `aio_run(...)` or equivalent) to invoke `agent_loop` and await its result.

## Acceptance Criteria
- Project path: /home/user/myproject
- Worker start command: `python3 /home/user/myproject/worker.py`
- Trigger command: `python3 /home/user/myproject/trigger.py`
- The task must be registered with Hatchet under the exact name `agent_loop`.
- The durable pause between turns must be performed via Hatchet's durable-sleep API, not via a process-local sleep.
- Running the trigger command (after the worker is started in the background) must print exactly one line to stdout in the format `RESULT: <json>`, where `<json>` is a JSON object containing:
  - `messages`: an array of `{role, content}` objects with length 4 (1 user + 3 assistant).
  - `turns`: the integer `3`.
  - `start_ts`, `end_ts`, `elapsed_ms`: integers with `end_ts - start_ts == elapsed_ms` and `elapsed_ms >= 2000`.
  - Each assistant message's `content` must start with the prefix `<idx>: ` for some integer index `<idx>` matching the turn number, and the 3rd assistant message must end with `[DONE]`.

