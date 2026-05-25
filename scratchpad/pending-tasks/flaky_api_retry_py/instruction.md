# Hatchet: Flaky API Retry

Define a Hatchet task `fetch_data` that fetches `http://localhost:9001/unstable` with exponential backoff retries; succeed within 5 attempts.

- Project path: `/home/user/project`
- Worker start command: `python worker.py`
- Trigger command: `python trigger.py`
  - Triggers the `fetch_data` task, waits for the run to complete, and prints the final JSON result on a single line of stdout.

A local Hatchet engine (hatchet-lite + Postgres) is already running in the container; the Hatchet SDK is preconfigured via the `HATCHET_CLIENT_TOKEN` and `HATCHET_CLIENT_TLS_STRATEGY` env vars.
