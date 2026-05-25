# Configure a Hatchet Worker with a Custom Slot Count (Python)

## Background
Hatchet workers expose a fixed pool of execution **slots** that control how many task runs a single worker process may execute concurrently. The slot count is reported back to the Hatchet server when the worker registers, and operators can inspect it through the Hatchet REST API. In this environment a local `hatchet-lite` server is running, the `hatchet-sdk` Python package is installed, and authentication environment variables (`HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_TLS_STRATEGY`, `HATCHET_CLIENT_HOST_PORT`, `HATCHET_CLIENT_SERVER_URL`, `HATCHET_CLIENT_TENANT_ID`) are pre-populated. Your job is to author a small Python worker that registers with the Hatchet server using a non-default slot capacity so the server records it correctly.

## Requirements
- Define a single Hatchet task named `noop` using the `@hatchet.task` decorator from `hatchet_sdk`. The task takes no meaningful input and must return the dict `{"ok": True}`.
- Create a worker named `slot-worker` and register the `noop` task on it.
- The worker **must** declare a slot capacity of exactly **5** (i.e. it must be created with `slots=5`) so the Hatchet server records its limit as 5.
- The worker must be startable as a foreground process via `python worker.py` from the project directory; once started it must connect to the local Hatchet server and stay alive long enough for the registration to be visible through the REST API.

## Implementation Hints
- The Hatchet SDK automatically reads `HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_TLS_STRATEGY`, and `HATCHET_CLIENT_HOST_PORT` when you instantiate `Hatchet()`.
- Look at `hatchet.worker(...)` in the Python SDK docs for the parameter that controls the worker's standard slot pool.
- Pass the `workflows=[...]` argument so the `noop` task is associated with the worker at registration time.
- Call `worker.start()` at module load only when the file is executed as a script (i.e. behind an `if __name__ == "__main__":` guard) so the verifier can also import `worker.py` without it starting a worker.

## Acceptance Criteria
- Project path: /home/user/myproject
- Start command: `python worker.py` (run from `/home/user/myproject`)
- The Python module `/home/user/myproject/worker.py` must exist and be importable. It must expose:
  - a module-level `hatchet` attribute (an instance of `hatchet_sdk.Hatchet`),
  - a module-level `noop` task object whose registered name is `noop`.
- When `python worker.py` is launched from `/home/user/myproject`, the worker connects to the local Hatchet server and registers itself with:
  - worker name `slot-worker`,
  - a standard slot capacity equal to **5**.
- The slot capacity must be observable through the Hatchet REST API. A `GET` request to `${HATCHET_CLIENT_SERVER_URL}/api/v1/tenants/${HATCHET_CLIENT_TENANT_ID}/worker` authenticated with `Authorization: Bearer ${HATCHET_CLIENT_TOKEN}` must include an entry whose `name` equals `slot-worker` and whose advertised slot limit (e.g. `maxRuns`, or the `limit` of the standard entry inside `slotConfig`) equals 5.
- The `noop` task, when triggered with an empty input, returns the JSON object `{"ok": true}`.

