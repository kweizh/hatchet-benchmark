"""
Hatchet sticky worker assignment demo — 3-step DAG (step_a → step_b → step_c).

Two worker processes (worker-A-<run_id> and worker-B-<run_id>) are spawned as
separate OS processes.  Because the workflow is declared with
StickyStrategy.SOFT the Hatchet scheduler will try to run all three tasks on the
same worker.

Each task appends one line to /tmp/run_steps.log:
    step=<name> worker_id=<WORKER_ID> hostname=<hostname> pid=<pid>

After the workflow completes the runner writes /tmp/result.json:
    {"worker_ids": ["<id_for_step_a>", "<id_for_step_b>", "<id_for_step_c>"]}
"""

from __future__ import annotations

import datetime
import json
import multiprocessing
import os
import socket
import sys
import time

LOG_FILE = "/tmp/run_steps.log"
RESULT_FILE = "/tmp/result.json"

# ---------------------------------------------------------------------------
# Task helpers (must be importable in spawned child processes)
# ---------------------------------------------------------------------------


def _write_log(step_name: str) -> dict:
    """Append one line to the shared log file and return the worker id dict."""
    worker_id = os.environ.get("WORKER_ID", "unknown")
    hostname = socket.gethostname()
    pid = os.getpid()

    line = (
        f"step={step_name} worker_id={worker_id} "
        f"hostname={hostname} pid={pid}\n"
    )
    with open(LOG_FILE, "a") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())

    print(f"[{worker_id}] executed {step_name} (pid={pid})", flush=True)
    return {"worker_id": worker_id}


# ---------------------------------------------------------------------------
# Worker subprocess entry-point
# ---------------------------------------------------------------------------


def _run_worker(worker_id: str, workflow_name: str) -> None:
    """
    Runs inside a child process.  Creates its own Hatchet client, registers
    the DAG workflow, and starts the worker (blocks until terminated).
    """
    os.environ["WORKER_ID"] = worker_id

    from hatchet_sdk import Context, Hatchet, StickyStrategy

    hatchet = Hatchet()

    wf = hatchet.workflow(
        name=workflow_name,
        sticky=StickyStrategy.SOFT,
    )

    @wf.task(
        name="step_a",
        execution_timeout=datetime.timedelta(seconds=120),
        schedule_timeout=datetime.timedelta(minutes=3),
    )
    def step_a(input, ctx: Context):
        return _write_log("step_a")

    @wf.task(
        name="step_b",
        parents=[step_a],
        execution_timeout=datetime.timedelta(seconds=120),
        schedule_timeout=datetime.timedelta(minutes=3),
    )
    def step_b(input, ctx: Context):
        return _write_log("step_b")

    @wf.task(
        name="step_c",
        parents=[step_b],
        execution_timeout=datetime.timedelta(seconds=120),
        schedule_timeout=datetime.timedelta(minutes=3),
    )
    def step_c(input, ctx: Context):
        return _write_log("step_c")

    worker = hatchet.worker(
        name=worker_id,
        slots=10,
        workflows=[wf],
    )
    worker.start()  # blocks


# ---------------------------------------------------------------------------
# Log-file parser
# ---------------------------------------------------------------------------


def _parse_log() -> dict[str, str]:
    """Return {step_name: worker_id} from /tmp/run_steps.log."""
    result: dict[str, str] = {}
    try:
        with open(LOG_FILE) as fh:
            for raw in fh:
                line = raw.strip()
                if not line:
                    continue
                parts = dict(
                    tok.split("=", 1) for tok in line.split() if "=" in tok
                )
                step = parts.get("step", "")
                wid = parts.get("worker_id", "")
                if step and wid:
                    result[step] = wid
    except FileNotFoundError:
        pass
    return result


# ---------------------------------------------------------------------------
# Runner (main process)
# ---------------------------------------------------------------------------


def main() -> None:
    run_id = os.environ.get("ZEALT_RUN_ID", "default")
    workflow_name = f"sticky-dag-{run_id}"
    worker_a_id = f"worker-A-{run_id}"
    worker_b_id = f"worker-B-{run_id}"

    # Clear the log file at the start of the run
    open(LOG_FILE, "w").close()

    # ── spawn worker-A ──────────────────────────────────────────────────────
    proc_a = multiprocessing.Process(
        target=_run_worker,
        args=(worker_a_id, workflow_name),
        daemon=True,
        name="hatchet-worker-A",
    )
    # ── spawn worker-B ──────────────────────────────────────────────────────
    proc_b = multiprocessing.Process(
        target=_run_worker,
        args=(worker_b_id, workflow_name),
        daemon=True,
        name="hatchet-worker-B",
    )

    proc_a.start()
    print(f"[runner] worker-A started  pid={proc_a.pid}", flush=True)

    proc_b.start()
    print(f"[runner] worker-B started  pid={proc_b.pid}", flush=True)

    # Wait for both workers to connect and register their workflow with Hatchet
    wait_secs = 20
    print(f"[runner] Waiting {wait_secs}s for workers to register …", flush=True)
    time.sleep(wait_secs)

    if not proc_a.is_alive():
        raise RuntimeError("worker-A crashed before the workflow was triggered")
    if not proc_b.is_alive():
        raise RuntimeError("worker-B crashed before the workflow was triggered")

    # ── trigger the workflow from the runner process ────────────────────────
    # We use the low-level admin client so we do NOT re-register the workflow
    # (which would create a conflicting definition).
    from hatchet_sdk import Hatchet

    hatchet = Hatchet()
    admin = hatchet._client.admin

    print(f"[runner] Triggering workflow '{workflow_name}' …", flush=True)
    run_ref = admin.run_workflow(
        workflow_name=workflow_name,
        input=None,
    )
    print(f"[runner] Workflow run id: {run_ref.workflow_run_id}", flush=True)

    # Block until the workflow finishes (result() polls until done)
    print("[runner] Waiting for workflow to complete …", flush=True)
    run_result = run_ref.result()
    print(f"[runner] Workflow result: {run_result}", flush=True)

    # ── extract per-step worker ids ─────────────────────────────────────────
    # The result dict has readable_id keys (task names) mapped to task output.
    def _pick(key: str) -> str:
        for k, v in run_result.items():
            if k == key or k.endswith(f":{key}"):
                if isinstance(v, dict):
                    return v.get("worker_id", "")
        return ""

    id_a = _pick("step_a")
    id_b = _pick("step_b")
    id_c = _pick("step_c")

    # Fall back to the log file if task outputs were empty
    if not (id_a and id_b and id_c):
        log_map = _parse_log()
        id_a = id_a or log_map.get("step_a", "")
        id_b = id_b or log_map.get("step_b", "")
        id_c = id_c or log_map.get("step_c", "")

    summary = {"worker_ids": [id_a, id_b, id_c]}
    with open(RESULT_FILE, "w") as fh:
        json.dump(summary, fh)

    print(f"[runner] Wrote {RESULT_FILE}: {summary}", flush=True)

    # ── shut down workers ───────────────────────────────────────────────────
    for proc in (proc_a, proc_b):
        if proc.is_alive():
            proc.terminate()
    for proc in (proc_a, proc_b):
        proc.join(timeout=10)
        if proc.is_alive():
            proc.kill()

    print("[runner] All workers terminated.  Done.", flush=True)
    sys.exit(0)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 'spawn' gives each child a clean Python interpreter — essential because
    # asyncio event loops cannot be safely shared or forked.
    multiprocessing.set_start_method("spawn", force=True)
    main()
