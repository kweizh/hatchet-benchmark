# Multi-Task Worker Registration with Hatchet (Python)

## Background
Hatchet is a distributed task queue and workflow engine. A single worker process can register and serve multiple independent tasks at once. In this task, you will define three arithmetic tasks, register them all on the same worker, start that worker against a real Hatchet server, then trigger each task once and record the results.

## Requirements
- Implement three Hatchet tasks in Python using the `hatchet-sdk` package:
  - An addition task that takes two integers `a` and `b` and returns their sum.
  - A subtraction task that takes two integers `a` and `b` and returns `a - b`.
  - A multiplication task that takes two integers `a` and `b` and returns their product.
- Register all three tasks on a single Hatchet worker process and start that worker.
- Trigger each task once with sample inputs and append the results to a log file.

## Implementation Hints
- Use the `Hatchet` client from `hatchet_sdk`. The server connection details come from `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` environment variables.
- Task names must be deterministic but unique per run; read `ZEALT_RUN_ID` from the environment and embed it into the task names so concurrent runs do not collide.
- A single `hatchet.worker(...)` call accepts a `workflows=[...]` argument that lists every task object to serve.
- Define typed inputs with a pydantic `BaseModel` (e.g. fields `a: int`, `b: int`).
- The worker call `worker.start()` blocks. To trigger tasks and then exit, start the worker in a background thread and call `task.run(input)` from the main thread to invoke each task synchronously.
- Make sure the worker is allowed enough time to register with the Hatchet server before you trigger the first task.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The script must connect to a real Hatchet server using the `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` environment variables. Do NOT mock the Hatchet server.
- The three task names must be suffixed with the value of the `ZEALT_RUN_ID` environment variable using the following base names:
  - Addition task name: `math-add-${ZEALT_RUN_ID}`
  - Subtraction task name: `math-subtract-${ZEALT_RUN_ID}`
  - Multiplication task name: `math-multiply-${ZEALT_RUN_ID}`
- All three tasks must be registered on the same worker. The worker name must be `math-worker-${ZEALT_RUN_ID}`.
- The script must trigger each task at least once against the running worker and write each result on its own line in the log file using exactly this format:
  - `Task <task_name> result: <integer_result>`
- After all three tasks have been triggered and logged, the script must exit cleanly (return code 0).
- After execution, querying the Hatchet server (for example via `hatchet.workflows.list()`) must return entries for all three task names.

