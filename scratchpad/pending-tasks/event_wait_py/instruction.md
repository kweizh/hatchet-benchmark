# Hatchet Durable Event Wait with Python SDK

## Background
Hatchet supports **durable execution** through `durable_task` functions that can pause and resume across worker restarts. A common pattern is for a task to wait until either an external event arrives, or a timeout elapses, using an OR-group of conditions on `ctx.aio_wait_for(...)`. This is the foundation for human-in-the-loop workflows.

In this task, you will build a minimal Python program that uses the `hatchet-sdk` package against the managed Hatchet Cloud control plane. A durable task `onboarding_flow` waits for *either* a `user:profile_completed` event *or* a 30-second sleep, whichever comes first. A runner triggers the workflow, then pushes the event a few seconds later so the event branch resolves first.

You MUST use Hatchet Cloud only (the default server endpoint baked into the SDK). Do NOT configure a custom `HATCHET_CLIENT_HOST_PORT`, `server_url`, or any other server-address override.

## Requirements
- Use the `hatchet-sdk` Python package to define a durable task named `onboarding_flow`.
  - It must take no required input fields (use `EmptyModel` or equivalent).
  - As its very first action, it must append the line `onboarding_flow started\n` to `/tmp/events.log`.
  - It must then call `ctx.aio_wait_for(...)` (the durable wait API on the `DurableContext`) with an OR group of two alternatives:
    1. A `SleepCondition` with a 30-second duration.
    2. A `UserEventCondition` with `event_key="user:profile_completed"`.
  - Inspect the resolved condition. If the `user:profile_completed` event resolved the wait first, return `{"status": "completed_via_event"}`. Otherwise return `{"status": "completed_via_timeout"}`.
- Write a runner script that:
  1. Reads `ZEALT_RUN_ID` from the environment.
  2. Creates a Hatchet worker whose worker name is `event-wait-worker-${ZEALT_RUN_ID}`, registers the `onboarding_flow` durable task on it, and starts it (in a background thread/process) so the durable task can execute.
  3. Triggers exactly one run of `onboarding_flow` against Hatchet Cloud.
  4. Approximately 5 seconds after triggering the run, pushes the `user:profile_completed` event via `hatchet.event.push("user:profile_completed", {})` (or the async equivalent `hatchet.event.aio_push(...)`).
  5. Waits for the run to finish, writes the task's final output (a JSON object containing the `status` field) to `/tmp/result.json` as valid JSON.
  6. Shuts down the worker cleanly and exits with code 0.
- The result must come from an actual Hatchet Cloud durable task run (no mocking, no local function-call shortcut). The wait must go through Hatchet's real durable event/wait infrastructure.

## Implementation Hints
- Authentication uses the `HATCHET_CLIENT_TOKEN` environment variable (already set). Do NOT hardcode any token value.
- Do NOT set a server address. The default endpoint in the SDK points at Hatchet Cloud; leave it alone.
- The durable-wait API in Python lives on `DurableContext`. The relevant primitives are `ctx.aio_wait_for(signal_key, *conditions)`, and the helpers `SleepCondition`, `UserEventCondition`, and `or_` for grouping alternatives.
- The result of `ctx.aio_wait_for(...)` is a dict shaped like `{"CREATE": {"<condition_key>": ...}}`. The `<condition_key>` for a `UserEventCondition` is the event key (e.g. `user:profile_completed`), which is how you decide whether the event or the timeout resolved the wait.
- Make sure the worker is actually running before pushing the event, otherwise the durable task will not be ready to receive it. Starting the worker in a background thread and then sleeping briefly before triggering the workflow is a reasonable approach.
- The script must terminate after the result is written; do not leave the worker process blocking forever.
- Install dependencies with `pip install hatchet-sdk` (already preinstalled in the environment).

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log (runner stdout/stderr is appended here when executed by the grader)
- Events log: /tmp/events.log (must contain the line `onboarding_flow started`, written from inside the durable task as its first action)
- Result file: /tmp/result.json
- The result file at `/tmp/result.json` must be valid JSON and contain a top-level field `status` whose value is exactly the string `completed_via_event`.
- The task and worker must be created using the `hatchet-sdk` Python package, registered against Hatchet Cloud (default server), and authenticated using the `HATCHET_CLIENT_TOKEN` environment variable read from the real environment.
- The worker name registered on Hatchet Cloud must be `event-wait-worker-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.

