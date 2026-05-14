# Hatchet Input Validation with Pydantic

## Background
Hatchet relies heavily on Pydantic in Python to validate inputs and outputs for durable tasks and DAG workflows. Improperly typed inputs should fail gracefully before the task logic executes.

## Requirements
- Initialize a Python project in `/home/user/app`.
- Create a Hatchet workflow named `DataProcessor` in `/home/user/app/workflow.py`.
- Define a Pydantic model `ProcessInput` with `user_id` (int), `email` (string, valid email format), and `score` (float between 0.0 and 100.0).
- Define a Pydantic model `ProcessOutput` with `status` (string, must be 'success' or 'failed') and `message` (string).
- Create a step `process_data` in the workflow that takes `ProcessInput` and returns `ProcessOutput`. It should return `status='success'` and a message containing the `user_id`.

## Constraints
- Project path: /home/user/app
- You must use `hatchet-sdk` and `pydantic`.
- Define the workflow correctly using Hatchet's decorators.