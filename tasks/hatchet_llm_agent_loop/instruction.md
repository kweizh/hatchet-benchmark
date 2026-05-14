# LLM Agent Loop with Hatchet Streaming

## Background
Hatchet is a distributed task queue and workflow engine that provides durable execution and streaming capabilities. You need to create an LLM-powered agent loop that uses durable execution to iterate until a "goal reached" condition is met, streaming progress back to the caller at each step.

## Requirements
- Initialize a Python project in `/home/user/agent_loop`.
- Use the `hatchet-sdk` to create a worker and a workflow/task named `agent_loop`.
- The task must implement an agent loop that runs up to 5 iterations.
- In each iteration, call a mock function `simulate_llm_call(step: int)` that returns a thought string and a boolean `goal_reached` (e.g., reached on step 3).
- Stream the `thought` back to the caller using Hatchet's streaming API (`aio_put_stream`).
- If `goal_reached` is true, break the loop and return the final result.
- If false, use an asynchronous sleep to simulate processing time before the next iteration.
- Create a script `run.py` that triggers the `agent_loop` task, subscribes to the stream, and writes all received stream chunks to `output.log`.

## Constraints
- Project path: `/home/user/agent_loop`
- Log file: `/home/user/agent_loop/output.log`
- Use the Python `hatchet-sdk`.
- Do not use fake Hatchet dependencies; connect to the real Hatchet engine.

## Integrations
- None