# Hatchet Cron Workflow

## Background
You need to set up a scheduled background job using Hatchet. The job will run periodically and process a batch of records from a file.

## Requirements
- Create a Hatchet workflow named `BatchProcessor`.
- The workflow should be scheduled to run every minute (`* * * * *`).
- The workflow should have a single task `process_records` that reads a JSON file containing a list of records and appends a line to a log file indicating how many records were processed.

## Implementation Guide
1. Create a Python script `/home/user/app/worker.py`.
2. Initialize the Hatchet client and define a workflow with `@hatchet.workflow(on_crons=["* * * * *"])`.
3. Define a task inside the workflow that reads `/home/user/app/records.json` and appends `Processed X records` to `/home/user/app/output.log`.
4. Start the Hatchet worker in the script.

## Constraints
- Project path: `/home/user/app`
- Log file: `/home/user/app/output.log`
- Use `hatchet-sdk` for Python.
- Ensure the Hatchet API token is loaded from the environment (`HATCHET_CLIENT_TOKEN`).