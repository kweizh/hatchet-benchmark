# Hatchet Durable Execution and Failure Recovery

## Background
Hatchet is a distributed task queue that supports "durable execution". Durable tasks can survive worker crashes and restarts by checkpointing progress (e.g., when spawning child tasks or waiting). You will implement a durable task that crashes midway, and verify it resumes correctly upon worker restart without re-executing completed steps.

## Requirements
1. Create a Hatchet worker in `/home/user/project/worker.py` that registers a durable task named `failure_recovery_task`.
2. The task must perform two logical steps:
   - **Step 1**: Append the string `step1\n` to `/home/user/project/output.log`.
   - **Crash**: Check if `/home/user/project/crashed.flag` exists. If it does not exist, create it, and forcefully crash the worker process using `os._exit(1)`.
   - **Step 2**: If the crash flag exists, append the string `step2\n` to `/home/user/project/output.log` and return.
3. Because the task must be durable, when it recovers from the crash, it must **NOT** execute Step 1 again. You must use Hatchet's durable execution primitives (e.g., spawning a child task for Step 1) to ensure `step1\n` is only written exactly ONCE to the log file.
4. Create a bash script `/home/user/project/run.sh` that runs the worker in a continuous `while true` loop, so that if it crashes, it automatically restarts.
5. Create a Python script `/home/user/project/trigger.py` that triggers `failure_recovery_task` and synchronously waits for it to complete.

## Constraints
- Project path: `/home/user/project`
- Log file: `/home/user/project/output.log`
- You must use the `hatchet-sdk` package in Python.
- Do NOT mock Hatchet; use the real Hatchet Cloud API via the `HATCHET_CLIENT_TOKEN` environment variable, which is already set in the environment.
- Ensure your code is executable and handles the crash and recovery autonomously.

## Integrations
- Hatchet Cloud (via `HATCHET_CLIENT_TOKEN`)