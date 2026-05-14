# Basic Hatchet DAG Workflow

## Background
Hatchet is a distributed task queue and workflow engine. Workflows can be defined as Directed Acyclic Graphs (DAGs) where tasks declare dependencies on other tasks.

## Requirements
- Create a Python script `worker.py` that defines a Hatchet DAG workflow named `SimpleDAG`.
- The workflow must have two tasks:
  - `step1`: Takes an input dictionary with a `message` key. It should return a dictionary with a `data` key containing the same message.
  - `step2`: Depends on `step1`. It should read the `data` output from `step1`, append the string `" World!"` to it, and return a dictionary with a `result` key.
- The `worker.py` script should start the Hatchet worker listening for this workflow.
- Create a `trigger.py` script that initializes a Hatchet client, triggers the `SimpleDAG` workflow with `{"message": "Hello"}`, waits for the workflow to complete, and writes the `result` from `step2` to a file named `output.txt`.

## Constraints
- Project path: `/home/user/project`
- Log file: `/home/user/project/output.txt`
- Use the `hatchet-sdk` package.
- The environment provides `HATCHET_CLIENT_TOKEN` to connect to Hatchet Cloud.

## Integrations
- Hatchet