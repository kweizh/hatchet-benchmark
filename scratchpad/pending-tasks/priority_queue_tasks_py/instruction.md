# Hatchet Priority Queue Run Ordering (Python SDK)

## Background
Hatchet supports per-run priorities so that higher-priority enqueued tasks of the same workflow are picked up before lower-priority ones. With workers limited to a single concurrency slot, the priority order is observable end-to-end: only one run executes at a time and the scheduler must pick the next run from the queue in priority order. In this task you will demonstrate Hatchet's `priority` feature against a real Hatchet server by enqueueing several runs in quick succession and showing that high-priority runs are processed before low-priority ones.

## Requirements
- Use the Hatchet Python SDK (`hatchet-sdk` installed via `pip3`).
- Define a Hatchet standalone task that accepts an input with an `id` field and **appends `<input.id>` as a single line** to the project log file each time it runs.
- Register the task on a Hatchet worker configured with **`slots=1`** so only one run can execute at a time.
- Trigger **six** runs of the task in quick succession against the real Hatchet server, using these `id`s and priorities:
  - 3 LOW-priority runs (priority value `1`) with ids `low-1`, `low-2`, `low-3`.
  - 3 HIGH-priority runs (priority value `3`) with ids `high-1`, `high-2`, `high-3`.
  - Submit the LOW runs first (in order) and the HIGH runs immediately after, without waiting for any run to finish between submissions.
- Wait for all six runs to finish, then stop the worker and exit cleanly.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the SDK reads these automatically).

## Implementation Hints
- Install the SDK with `pip3 install hatchet-sdk`.
- Declare the standalone task with `@hatchet.task(name=..., input_validator=...)`. The function should receive the input (an object/model with an `id` attribute) and a `Context`, and append `input.id + "\n"` to the log file.
- Build a worker via `hatchet.worker(...)` with `slots=1` and the task registered on it. Start the worker in a background thread or subprocess so the main process can submit triggers and then wait for completion.
- Trigger runs with priority via the SDK helpers. Examples:
  - `task.run_no_wait(input=..., options=TriggerWorkflowOptions(priority=1))` and `priority=3` for HIGH, or
  - `task.aio_run_no_wait(...)`, or `task.run(..., options=TriggerWorkflowOptions(priority=...))`.
- `TriggerWorkflowOptions` is importable from `hatchet_sdk`. Hatchet also exposes a `Priority` enum (`Priority.LOW == 1`, `Priority.HIGH == 3`).
- Submit all 6 triggers without awaiting each individual run before submitting the next, so the queue contains the remaining triggers when the worker picks the next item.
- After submission, wait for all 6 runs to finish (e.g., poll each run reference's result, or use `aio_result`/`result`).
- The task name registered with Hatchet must be unique per concurrent trial: read `ZEALT_RUN_ID` from the environment and use it as a suffix.
- The log file must accumulate exactly the 6 ids, one per line, in the order Hatchet ran them.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet task name: `priority-task-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The Hatchet worker that runs the task must be configured with `slots=1` so only one run executes at a time.
- Six runs MUST be triggered in quick succession: three with priority `1` (LOW) and `id` values `low-1`, `low-2`, `low-3` (submitted first, in that order), followed immediately by three with priority `3` (HIGH) and `id` values `high-1`, `high-2`, `high-3` (in that order).
- After all six runs complete, `/home/user/myproject/output.log` MUST contain exactly six non-empty lines, each line being one of the six ids above (`low-1`, `low-2`, `low-3`, `high-1`, `high-2`, `high-3`), with no other content. The order of lines reflects the order in which Hatchet executed the runs.
- The execution order in the log MUST demonstrate that priority is respected: among the last two lines, BOTH must be LOW-priority ids; and among the first four lines, AT LEAST three must be HIGH-priority ids (this accommodates the case where one LOW run may already be executing when the HIGH runs are enqueued).
- The task is invoked as a single one-off job (e.g., `python3 /home/user/myproject/main.py`) that exits cleanly after all six runs finish.

