# Hatchet TypeScript Worker

## Background
Hatchet is a distributed task queue and workflow engine designed for high-concurrency background jobs. In this task, you will set up a simple Hatchet worker using the TypeScript SDK that registers a workflow and processes an event.

## Requirements
- Initialize a Node.js project in `/home/user/app` with TypeScript.
- Install `@hatchet-dev/typescript-sdk`, `typescript`, `ts-node`, and `@types/node`.
- Create a Hatchet workflow in `worker.ts` that listens to the `user:create` event.
- The workflow should have a single step named `greet` that receives the event payload, extracts the `username` from the input, and returns `{ message: "Welcome " + username }`.
- Upon receiving the event, the `greet` step must also write the returned JSON object `{"message":"Welcome Alice"}` to `/home/user/app/output.log`.
- The `worker.ts` script should initialize Hatchet, create a worker named `test-worker`, register the workflow, and start the worker.
- Create a `trigger.ts` script that initializes Hatchet and pushes a `user:create` event with payload `{ username: "Alice" }`.
- Add npm scripts: `"worker": "npx ts-node worker.ts"` and `"trigger": "npx ts-node trigger.ts"`.

## Constraints
- Project path: /home/user/app
- Log file: /home/user/app/output.log
- A valid Hatchet instance is required. The environment variable `HATCHET_CLIENT_TOKEN` will be provided.