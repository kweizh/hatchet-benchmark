# Hatchet TypeScript: Basic Task

## Background
Hatchet is a distributed task queue and durable execution engine. In this task, you will implement a minimal Hatchet task using the official TypeScript SDK (`@hatchet-dev/typescript-sdk`). You will register a task on a worker, run it once from a runner script, and persist the result to disk so it can be verified.

## Requirements
- Create a Hatchet task that takes `{ name: string }` as input and returns `{ greeting: "Hello, <name>!" }`.
- The task must be registered under the name `simple-greeting-ts-${ZEALT_RUN_ID}` (read `ZEALT_RUN_ID` from the environment so concurrent trials do not collide).
- Implement two TypeScript entrypoints in the project:
  - `worker.ts` — registers the task and starts a worker.
  - `runner.ts` — triggers the task once with `{ name: "World" }`, awaits the result, and writes it as JSON to `/tmp/result.json`.
- Provide a `package.json` and `tsconfig.json` so the project can be executed with `tsx` (or compiled TypeScript).
- Use Hatchet Cloud. The default server address baked into the SDK is correct — do not override it. Authenticate using the `HATCHET_CLIENT_TOKEN` environment variable.

## Implementation Hints
- Initialize the client with `HatchetClient.init()` from `@hatchet-dev/typescript-sdk/v1`.
- Define the task with `hatchet.task({ name, fn })` and export it from a module imported by both `worker.ts` and `runner.ts` so the task name is identical on both sides.
- The worker is started with `await hatchet.worker(<worker-name>, { workflows: [<task>] }).start()`. Start the worker in the background before the runner triggers the task.
- The runner should `await <task>.run({ name: "World" })` and write the returned object to `/tmp/result.json` using `fs.writeFileSync` with `JSON.stringify`.
- Read `ZEALT_RUN_ID` from `process.env` and interpolate it into the task name on both sides.

## Acceptance Criteria
- Project path: /home/user/myproject
- The Hatchet task is registered under the name `simple-greeting-ts-${ZEALT_RUN_ID}` (where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable).
- After running the worker and the runner, the file `/tmp/result.json` exists and contains a JSON object with a `greeting` field equal to `Hello, World!`.
- The project uses the `@hatchet-dev/typescript-sdk` package and is runnable with Node.js (e.g. via `tsx`).

