# Define a Simple Hatchet Task in Python

## Background
Hatchet is a distributed task queue and workflow engine that lets developers define background work as durable, retryable tasks. A local Hatchet Lite server is running in this environment, an authentication token has already been generated for you, and the `hatchet-sdk` Python package is installed. Your job is to author a tiny `greet` task using the Python SDK and run a worker that registers the task with the local Hatchet server so it can be invoked.

## Requirements
- Implement a Python module that defines a single Hatchet task named `greet` using the `@hatchet.task` decorator from `hatchet_sdk`.
- The task input must be validated with a Pydantic model that contains a single field `name: str`.
- The task must return a `dict` shaped like `{"message": f"Hello {input.name}"}` (with a single space, no punctuation).
- Create a Hatchet worker named `greet-worker`, register the `greet` task on it, and start the worker so the task is registered with the local Hatchet server.

## Implementation Hints
- Read the connection settings from the pre-populated environment variables `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_TLS_STRATEGY`, and `HATCHET_CLIENT_HOST_PORT`. The Hatchet SDK picks them up automatically when you instantiate `Hatchet()`.
- Use a Pydantic `BaseModel` subclass as the `input_validator` argument (or via the task-function signature) so that the validated input is delivered to your function.
- Keep the worker startup compatible with a normal foreground run (e.g. `worker.start()`); the verifier will start the worker itself, so you do not need to leave it running yourself.

## Acceptance Criteria
- Project path: /home/user/myproject
- Worker entry point: `python worker.py` started from `/home/user/myproject` registers a Hatchet task named `greet` on a worker named `greet-worker` with the local Hatchet Lite server.
- The `greet` task accepts an input object with a single string field `name` and returns a JSON object with exactly one key `message`.
- When the task is triggered with `name="World"`, the returned object equals `{"message": "Hello World"}`.
- The Python file `/home/user/myproject/worker.py` must exist and be importable; the verifier will import its module-level `hatchet` client and `greet` task object to trigger the task.

