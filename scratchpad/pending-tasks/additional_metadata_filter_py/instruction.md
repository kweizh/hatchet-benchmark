# Hatchet: Filter Runs by Additional Metadata (Python SDK)

## Background
Hatchet lets you attach arbitrary key-value string metadata to task runs via the `additional_metadata` argument when triggering a run. Later you can query runs through the Hatchet REST API and filter them on those metadata pairs. This is the recommended pattern for tagging runs with business attributes (team, region, source, environment, etc.) and then auditing or counting them after the fact.

In this task you will use Hatchet's Python SDK to implement a tiny tagging task, trigger it three times with different `additional_metadata`, and then use the SDK's `runs.list(...)` API to count how many runs were tagged with a particular team. The count is written to a log file that the verifier will read.

## Requirements
- Implement a Hatchet **standalone task** in Python named `tag-record-${ZEALT_RUN_ID}` that simply returns the dictionary `{"ok": True}`.
- Register a worker for the task and start it (e.g. in a background thread) so the task can actually execute against the real Hatchet server.
- Trigger the task **three times** with different `additional_metadata`:
  - Two of the three triggers must use `additional_metadata = {"team": "alpha-${ZEALT_RUN_ID}"}`.
  - The remaining trigger must use `additional_metadata = {"team": "beta-${ZEALT_RUN_ID}"}`.
  - Each trigger MUST also set `additional_metadata["zealt_run_id"] = "${ZEALT_RUN_ID}"` so the runs can be uniquely identified per trial.
- Wait for all three runs to finish.
- Use the Hatchet Python SDK's `hatchet.runs.list(...)` to query runs filtered on the metadata pair `team=alpha-${ZEALT_RUN_ID}`, count how many runs match, and write the count to a log file.
- Connect to the real Hatchet server using the environment variables `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` (the Python SDK reads these automatically).

## Implementation Hints
- Install the Hatchet Python SDK via `pip3 install hatchet-sdk`.
- A standalone task can be declared with the `@hatchet.task(name=...)` decorator. The task function receives an input (e.g. `EmptyModel`) and a `Context` as positional arguments.
- To attach metadata when triggering, pass the `additional_metadata=` keyword argument to the task's `run` (or `run_no_wait`) method.
- To list runs by metadata, use `hatchet.runs.list(additional_metadata={"team": "alpha-..."})`. The returned object has a `rows` attribute you can iterate or count.
- Because tasks may run concurrently in the same Hatchet tenant, you MUST scope BOTH the task name and the metadata values with `ZEALT_RUN_ID` so different trials cannot see each other's runs. Read `ZEALT_RUN_ID` from the environment.
- A long-running worker process is required to actually execute the task. Use the SDK worker API to register the task and start the worker (in a background thread or subprocess), then trigger the three runs and wait for completion before writing the log file.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Log file: `/home/user/myproject/output.log`
- Hatchet task name: `tag-record-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The task is triggered exactly three times against the real Hatchet server (using `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL`) with the following `additional_metadata` distribution (in addition to a `zealt_run_id` key equal to `${ZEALT_RUN_ID}` on every run):
  - Run 1: `team=alpha-${ZEALT_RUN_ID}`
  - Run 2: `team=beta-${ZEALT_RUN_ID}`
  - Run 3: `team=alpha-${ZEALT_RUN_ID}`
- All three runs MUST finish successfully before the log file is written.
- The log file `/home/user/myproject/output.log` MUST contain:
  - Three lines, one per triggered run, each in the format: `Run id=<workflow_run_id> team=<team_value>` (the team value is the full `alpha-${ZEALT_RUN_ID}` / `beta-${ZEALT_RUN_ID}` string).
  - A final line in the format: `Alpha run count: <N>` where `<N>` is the number of runs returned by `hatchet.runs.list(additional_metadata={"team": "alpha-${ZEALT_RUN_ID}"})` (must equal 2 for a correct solution).

