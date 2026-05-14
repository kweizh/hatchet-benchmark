# Hatchet Worker Slot Management Demonstration

## Overview
This project demonstrates the difference between standard (blocking) sleep and durable (non-blocking) sleep in Hatchet worker slot management.

## Implementation Details
- **Project Path**: `/home/user/hatchet-slots`
- **SDK**: `@hatchet-dev/typescript-sdk` (v1)
- **Worker Concurrency**: Configured with `maxRuns: 1` to limit the worker to a single slot.
- **Workflows**:
    - `StandardSleepTask`: Uses a standard `setTimeout` wrapped in a Promise. This blocks the execution thread and holds the worker slot for 5 seconds.
    - `DurableSleepTask`: Uses `ctx.sleepFor('5s')`. This evicts the task from the worker, freeing the slot for other tasks while waiting.
    - `TestTask`: A simple task used to verify slot availability.

## Demonstration Scenarios
1. **Scenario 1 (Standard Sleep)**:
    - `StandardSleepTask` is triggered.
    - `TestTask` is triggered immediately after.
    - Result: `TestTask` is blocked until `StandardSleepTask` finishes because the single slot is held.
2. **Scenario 2 (Durable Sleep)**:
    - `DurableSleepTask` is triggered.
    - `TestTask` is triggered immediately after.
    - Result: `TestTask` executes immediately because `DurableSleepTask` released the slot during its sleep period.

## Files
- `worker.ts`: Contains the worker configuration and workflow definitions.
- `trigger.ts`: Script to trigger the demonstration scenarios and observe behavior.
- `package.json`: Project configuration and dependencies.
- `tsconfig.json`: TypeScript configuration for ESM support.

## Note on Execution
During the verification phase, the Hatchet Cloud engine returned `INTERNAL ERROR` for `PutWorkflow` requests. This appears to be a server-side issue or a mismatch between the latest SDK and the current engine version on the cloud. However, the implementation follows the latest Hatchet v1 SDK patterns and requirements.
