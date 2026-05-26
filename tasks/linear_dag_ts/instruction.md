# Hatchet Linear DAG (TypeScript)

## Background
Build a small Hatchet workflow using the `@hatchet-dev/typescript-sdk` (TypeScript SDK) that demonstrates a linear, 3-step Directed Acyclic Graph (DAG). Each step receives the output of its parent task via `ctx.parentOutput(...)` and transforms a piece of text. The workflow is registered on a worker, triggered by a runner script, and the final result is written to a JSON file on disk so it can be verified.

The Hatchet client must connect to Hatchet Cloud using the default server address (do not override the server URL). Authentication is performed exclusively via the real `HATCHET_CLIENT_TOKEN` environment variable.

## Requirements
- Implement a single Hatchet workflow named `linear-dag-${ZEALT_RUN_ID}` with exactly three tasks executed sequentially: `step1` -> `step2` -> `step3`.
- `step1` returns an object `{ text: "hello" }`.
- `step2` declares `step1` as its parent, reads the parent output via `ctx.parentOutput(step1)`, and returns `{ text: <parent.text> + " world" }`.
- `step3` declares `step2` as its parent, reads the parent output via `ctx.parentOutput(step2)`, and returns `{ final: <parent.text> + "!" }`.
- A worker script must register the workflow and run continuously.
- A runner script must trigger the workflow (fire-and-wait), capture the final `step3` output, and write it to `/tmp/result.json` as JSON.
- All side-effect-prone identifiers (workflow name, worker name) must be suffixed with the current `run-id` taken from the `ZEALT_RUN_ID` environment variable so concurrent trials do not collide.

## Implementation Hints
- Install the `@hatchet-dev/typescript-sdk` package and use `tsx` to run the worker and runner scripts.
- Create a Hatchet client with `new Hatchet()` (or the SDK's standard factory) so it picks up the `HATCHET_CLIENT_TOKEN` env var automatically. Do not set a custom server address; the SDK's default points at Hatchet Cloud.
- Declare the workflow with `hatchet.workflow({ name: ... })` and add tasks with `workflow.task({ name, parents, fn })`.
- Inside child tasks, get parent output via `await ctx.parentOutput(parentTaskRef)`.
- Start the worker with `hatchet.worker(<workerName>, { workflows: [workflow] })` followed by `await worker.start()`.
- In a separate runner script, call `await workflow.run({})` (or `.run({}, {})`) and write the returned `step3` task output to `/tmp/result.json` using `fs.writeFileSync`. The DAG run result is keyed by task name, so the final value can be retrieved as `result.step3` (or by reading the equivalent task-output field returned by the SDK).
- Read `ZEALT_RUN_ID` from `process.env.ZEALT_RUN_ID` and embed it in the workflow name and the worker name (e.g. `linear-dag-${runId}`, `linear-dag-worker-${runId}`).
- Add `npm` scripts (`worker`, `run`) that invoke `tsx` against the respective TypeScript entry files, so they can be triggered with `npm run ...`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Workflow name: `linear-dag-${ZEALT_RUN_ID}` (where `${ZEALT_RUN_ID}` is the value of the `ZEALT_RUN_ID` environment variable).
- Worker start command: `npm run worker` (must run a long-lived Hatchet worker registered with the workflow above).
- Runner command: `npm run run` (must trigger the workflow and wait for it to complete).
- The runner MUST write the final step's output to the file `/tmp/result.json` as a JSON object with the following shape:
  ```json
  {
    "final": string
  }
  ```
- After a successful end-to-end execution, `/tmp/result.json` MUST contain exactly `{"final": "hello world!"}` (whitespace insensitive).
- The Hatchet client/worker MUST authenticate using the real `HATCHET_CLIENT_TOKEN`; no mocking of the Hatchet service is allowed.

