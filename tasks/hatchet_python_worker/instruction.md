# Hatchet Python Worker Event Processing

## Background
Hatchet is a distributed task queue and workflow engine. You need to create a simple Python SDK worker that registers a workflow and processes an event.

## Requirements
- Initialize a Python project in `/home/user/hatchet-worker`.
- Create a Hatchet worker named `event-worker`.
- Register a workflow that listens to the `user:create` event.
- When the event is received, the workflow should write the event payload to `/home/user/hatchet-worker/output.json`.
- The worker script must be named `worker.py` and must be running to process events.
- Assume `HATCHET_CLIENT_TOKEN` is available in the environment.

## Constraints
- Project path: `/home/user/hatchet-worker`
- Output file: `/home/user/hatchet-worker/output.json`
- The worker must keep running (e.g., using `worker.start()`).