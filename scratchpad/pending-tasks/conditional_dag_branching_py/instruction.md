# Conditional DAG Branching with Hatchet (Python)

## Background
Hatchet is a distributed task queue and workflow engine that supports DAGs with conditional branching. Tasks in a DAG can declare `skip_if` parent conditions so that exactly one of a set of sibling branches runs on a given workflow execution. Downstream tasks can then inspect which parent ran (and which was skipped) using `ctx.was_skipped(...)`.

In this task, you will build an approval-flow DAG that branches on an input value, run it twice with different inputs, observe that two different branches execute, and record the results to a log file.

## Requirements
- Use the Python SDK `hatchet-sdk` and connect to the real Hatchet server using the `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` environment variables. NEVER mock the SDK or the server.
- Define a single Hatchet workflow whose name is `approval-flow-${ZEALT_RUN_ID}` (read `ZEALT_RUN_ID` from the environment).
- The workflow MUST contain exactly four tasks with the following names and DAG structure:
  - `root`: receives an input object with a single field `amount` (float). Returns `{ "amount": <amount>, "is_large": <amount > 100> }`.
  - `approve_path`: a child of `root`. MUST be skipped when the root output's `is_large` is `False`. Returns `{ "approved": true }`.
  - `auto_path`: a child of `root`. MUST be skipped when the root output's `is_large` is `True`. Returns `{ "auto": true }`.
  - `log_decision`: a child of BOTH `approve_path` and `auto_path`. It MUST detect which parent actually ran (vs was skipped) using the skip-aware context API and return `{ "decision": "approved" }` if `approve_path` ran, otherwise `{ "decision": "auto" }`.
- Start a worker, register the workflow, and trigger the workflow TWO times in a single program execution:
  - First run with input `{"amount": 50}` — `auto_path` should run and `approve_path` should be skipped.
  - Second run with input `{"amount": 500}` — `approve_path` should run and `auto_path` should be skipped.
- Wait until both runs reach a terminal state before exiting.
- Append two lines (in run order) to the log file `/home/user/myproject/output.log`, one per triggered workflow run, in the EXACT format:
  `amount=<amount> decision=<approved|auto> run_id=<workflow_run_id>`
  where `<amount>` is the integer `50` or `500` (no decimal point), `<decision>` is either `approved` or `auto`, and `<workflow_run_id>` is the unique run identifier returned by the Hatchet SDK when the workflow was triggered. There must be exactly one line for `amount=50` and exactly one line for `amount=500`.
- After both runs complete, the program MUST exit cleanly.

## Implementation Hints
- Pick any sensible mechanism (e.g., a background thread, async task group, or subprocess) to run the worker concurrently with the triggering / waiting logic, so the workflow can actually execute while you wait for results.
- Use the SDK's parent-condition primitive together with a CEL-style expression on the parent output to express "skip when `is_large` is False/True".
- For the join task, check whether each parent was skipped before reading its output; use that information to decide the final decision string.
- To retrieve a run's outputs after triggering, you can either await the run handle returned by the SDK, or look up the result by run ID through the runs API.
- Read `ZEALT_RUN_ID` from the environment and append it to the workflow name to keep concurrent runs isolated.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The workflow name registered against the Hatchet server is `approval-flow-${ZEALT_RUN_ID}` where `ZEALT_RUN_ID` is read from the environment.
- The log file MUST contain exactly two lines (no extra blank lines, no extra runs), each matching the format `amount=<int> decision=<approved|auto> run_id=<workflow_run_id>`.
- One line MUST be for `amount=50` with `decision=auto`.
- One line MUST be for `amount=500` with `decision=approved`.
- Each `<workflow_run_id>` in the log file MUST correspond to an actual completed run of the `approval-flow-${ZEALT_RUN_ID}` workflow on the Hatchet server, where:
  - The run with `amount=50` had `auto_path` run successfully and `approve_path` skipped.
  - The run with `amount=500` had `approve_path` run successfully and `auto_path` skipped.

