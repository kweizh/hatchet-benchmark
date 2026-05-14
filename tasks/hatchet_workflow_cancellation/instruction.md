# Hatchet Workflow Cancellation

## Background
Hatchet provides a mechanism for canceling task executions gracefully, allowing you to signal to running tasks that they should stop. This is useful for long-running tasks that may no longer be needed.

## Requirements
1. Create a Hatchet workflow named `cancellation_workflow` in `worker.py` with a task `check_flag`.
2. The task should loop 10 times, sleeping for 1 second each iteration.
3. In each iteration, it should check `ctx.exit_flag`. If True, it must print "Task has been cancelled" and raise a `ValueError("Task has been cancelled")`.
4. If the loop completes without cancellation, it should return `{"error": "Task should have been cancelled"}`.
5. The `worker.py` script must initialize a Hatchet client, create a worker named `cancel-worker`, register the workflow, and start the worker.
6. Create a script `trigger.py` that initializes a Hatchet client, triggers the `cancellation_workflow` asynchronously (fire-and-forget), sleeps for 2 seconds, and then cancels the workflow run using `hatchet.runs.cancel(...)`.
7. The `trigger.py` script must write the `workflow_run_id` of the triggered run to a file named `run_id.txt` in the project directory before exiting.

## Constraints
- Project path: `/home/user/myproject`
- Both scripts must be executable with `python3`.
- You must use the `hatchet-sdk` package.