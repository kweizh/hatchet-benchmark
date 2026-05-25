# Linear DAG Workflow with Hatchet (TypeScript)

## Background
[Hatchet](https://docs.hatchet.run) is a distributed task queue and workflow engine that supports defining DAG workflows declaratively. In this task you will build a three-step linear DAG in TypeScript where each task reads its parent's output and applies a string transformation, producing a final uppercase result.

A local self-hosted Hatchet Lite engine (engine + API + gRPC) is already running inside the container, backed by PostgreSQL. The required Hatchet client environment variables (`HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, `HATCHET_CLIENT_TLS_STRATEGY=none`) are pre-configured and exported automatically (they are sourced from `/etc/zealt/hatchet.sh` via `BASH_ENV`) so that any Hatchet SDK client can connect to the local engine without TLS.

## Requirements
- Use the official TypeScript SDK (`@hatchet-dev/typescript-sdk`) to define a workflow named `pipeline`.
- Add three tasks to the workflow that form a strict linear chain `step1 -> step2 -> step3`:
  - `step1`: no parent. Returns the object `{ data: 'hello' }`.
  - `step2`: parent is `step1`. Reads the parent's `data` value via `ctx.parentOutput(step1)` and returns `{ msg: <parent.data> + ' world' }`.
  - `step3`: parent is `step2`. Reads the parent's `msg` value via `ctx.parentOutput(step2)` and returns `{ final: <parent.msg>.toUpperCase() }`.
- Register the workflow on a worker and start the worker so it keeps running and accepting work.
- The worker must be runnable as a background process via the start command listed in Acceptance Criteria.

## Implementation Hints
- Initialize a Node.js (TypeScript) project under the project path. Install `@hatchet-dev/typescript-sdk` plus any TS runtime helpers you need (for example `ts-node` and `typescript`).
- Use `Hatchet.init()` to construct the client (it picks up `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, and `HATCHET_CLIENT_TLS_STRATEGY` from the environment).
- Declare the workflow with `hatchet.workflow({ name: 'pipeline' })`.
- Declare each task with `dag.task({ name, fn, ... })` and use the `parents: [...]` option to declare the dependency chain.
- Inside child tasks, read parent output with `ctx.parentOutput(parentTask)`.
- Register the workflow on a worker with `hatchet.worker('<worker-name>', { workflows: [pipeline] })` and then `await worker.start()`.
- The worker process must stay running in the foreground; the provided start command will be used both for verification and by external clients that trigger the workflow.

## Acceptance Criteria
- Project path: /home/user/myproject
- Start command: `npx ts-node worker.ts`
- The project directory must contain a `worker.ts` file at the root, along with a valid `package.json` that declares `@hatchet-dev/typescript-sdk` as a dependency.
- After running `npm install`, starting the worker with the start command above must:
  - Connect successfully to the local Hatchet server using only environment variables (no hard-coded tokens or addresses).
  - Register a workflow named `pipeline` containing the three tasks `step1`, `step2`, and `step3` with the dependency chain `step1 -> step2 -> step3`.
  - Keep the worker running in the foreground so additional workflow runs are accepted.
- When the `pipeline` workflow is triggered through any Hatchet SDK (with no input or an empty input object), the workflow must complete successfully and the output of `step3` must equal `{ "final": "HELLO WORLD" }`.

