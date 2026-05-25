# Define and Register a Simple Hatchet Task with the TypeScript SDK

## Background
Hatchet is a distributed task queue and durable workflow engine. The local environment already runs a self-hosted Hatchet Lite server (engine + API + gRPC) backed by PostgreSQL. The `HATCHET_CLIENT_TOKEN` and related connection environment variables are pre-configured so that any Hatchet SDK client can connect to the local engine without TLS.

You need to define a small Hatchet task using the official TypeScript SDK (`@hatchet-dev/typescript-sdk`), register it on a worker, and start the worker so the task can be invoked by other clients (for example, the Python SDK acting as a trigger).

## Requirements
- Use the TypeScript SDK to declare a task named `uppercase`.
- The task receives an input object with a `text` field (string) and must return an object of shape `{ result: <uppercased text> }`.
- Register the task on a worker named `ts-worker` and start it so the worker stays connected to the local Hatchet server and continues to accept work.
- The worker must be runnable as a background process via the start command listed in Acceptance Criteria.

## Implementation Hints
- Initialize a Node.js project (TypeScript) under the project path and install `@hatchet-dev/typescript-sdk` plus any TS runtime helpers you need (for example `ts-node` and `typescript`).
- Use `Hatchet.init()` to construct the client. The required `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_TLS_STRATEGY=none` are provided by the environment.
- Define the task with `hatchet.task({ name, fn })`, register it via `hatchet.worker('ts-worker', { workflows: [task] })`, then `await worker.start()`.
- The worker needs to keep running after it is started; the provided start command will be used both for verification and by external clients that trigger the task.

## Acceptance Criteria
- Project path: /home/user/myproject
- Start command: npx ts-node worker.ts
- The project directory must contain a `worker.ts` file at the root, along with a valid `package.json` that declares `@hatchet-dev/typescript-sdk` as a dependency.
- After running `npm install`, starting the worker with the start command above must:
  - Connect successfully to the local Hatchet server using only environment variables (no hard-coded tokens or addresses).
  - Register a task named `uppercase` on a worker named `ts-worker`.
  - Keep the worker running in the foreground so additional task runs are accepted.
- When the `uppercase` task is invoked through any Hatchet SDK with input `{ text: <string> }`, the worker must return an output object whose `result` field equals the uppercase version of the input `text`.

