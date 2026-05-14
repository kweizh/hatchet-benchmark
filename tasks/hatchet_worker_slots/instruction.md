# Hatchet Worker Slot Management

## Background
Hatchet is a distributed task queue and workflow engine. A key concept in Hatchet is understanding how worker slots are managed. In a standard task, a long-running wait (e.g., using a standard sleep or `ctx.sleep` if available, or native sleep) holds the worker slot, preventing other tasks from running if the worker is at capacity. In contrast, a durable task using `ctx.sleepFor` evicts the task and frees the worker slot, allowing other tasks to execute concurrently.

## Requirements
- Initialize a TypeScript project in `/home/user/hatchet-slots` and install `@hatchet-dev/typescript-sdk`.
- Create a Hatchet worker configured with a concurrency limit of 1 (only 1 slot available).
- Implement a standard workflow task `StandardSleepTask` that sleeps for 5 seconds using a standard blocking wait (e.g., `setTimeout` wrapped in a Promise).
- Implement a durable task `DurableSleepTask` that sleeps for 5 seconds using `ctx.sleepFor('5s')`.
- Create a script `trigger.ts` that demonstrates the difference:
  - Trigger `StandardSleepTask` and immediately trigger another task `TestTask`.
  - `TestTask` should be blocked until `StandardSleepTask` finishes because the slot is held.
  - Trigger `DurableSleepTask` and immediately trigger another `TestTask`.
  - `TestTask` should execute immediately because `DurableSleepTask` frees the slot.

## Constraints
- Project path: /home/user/hatchet-slots
- Start command: `npx ts-node trigger.ts` (or compile and run)
- Use the real Hatchet API key from the environment (`HATCHET_CLIENT_TOKEN`).
- Do not provide an implementation guide in the instruction.

## Integrations
- None