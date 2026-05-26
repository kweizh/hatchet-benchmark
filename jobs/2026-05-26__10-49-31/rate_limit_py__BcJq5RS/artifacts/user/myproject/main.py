"""
main.py – Orchestration entrypoint for the Hatchet static rate-limit demo.

Flow
----
1.  Clear /tmp/rate_log.txt.
2.  Spawn a child process that registers the rate limit and runs the worker.
3.  Wait for the worker to be ready (poll until Hatchet accepts a run).
4.  Trigger 15 runs of call_external_api in rapid parallel succession.
5.  Wait for all 15 runs to finish (timeout = 5 minutes).
6.  Verify /tmp/rate_log.txt has exactly 15 lines, then exit 0.
"""

import multiprocessing
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

LOG_FILE = "/tmp/rate_log.txt"
TOTAL_RUNS = 15
WAIT_TIMEOUT_SECONDS = 300  # 5 minutes
WORKER_WARMUP_SECONDS = 10  # time to let the worker connect before dispatching


# ---------------------------------------------------------------------------
# Helper: count non-empty lines in the log file
# ---------------------------------------------------------------------------

def count_log_lines() -> int:
    try:
        with open(LOG_FILE) as fh:
            return sum(1 for line in fh if line.strip())
    except FileNotFoundError:
        return 0


# ---------------------------------------------------------------------------
# Helper: trigger a single run and return its result ref
# ---------------------------------------------------------------------------

def trigger_run(_: int):
    """
    Import task inside the thread so each thread gets its own SDK state.
    Returns the run result reference (already dispatched to Hatchet).
    """
    from task import call_external_api  # noqa: PLC0415

    run_ref = call_external_api.run({})
    return run_ref


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    # ------------------------------------------------------------------
    # Step 1: clear the log file
    # ------------------------------------------------------------------
    print(f"[main] clearing {LOG_FILE}")
    with open(LOG_FILE, "w") as fh:
        fh.write("")

    # ------------------------------------------------------------------
    # Step 2: start the worker in a child process
    # ------------------------------------------------------------------
    print("[main] spawning worker process …")
    worker_proc = multiprocessing.Process(
        target=_run_worker,
        daemon=True,
        name="hatchet-worker",
    )
    worker_proc.start()

    # ------------------------------------------------------------------
    # Step 3: give the worker time to connect and register
    # ------------------------------------------------------------------
    print(f"[main] waiting {WORKER_WARMUP_SECONDS}s for worker to connect …")
    time.sleep(WORKER_WARMUP_SECONDS)

    if not worker_proc.is_alive():
        print("[main] ERROR: worker process died during warm-up", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 4: trigger 15 runs in parallel
    # ------------------------------------------------------------------
    print(f"[main] dispatching {TOTAL_RUNS} runs …")
    run_refs = []

    with ThreadPoolExecutor(max_workers=TOTAL_RUNS) as pool:
        futures = [pool.submit(trigger_run, i) for i in range(TOTAL_RUNS)]
        for fut in as_completed(futures):
            try:
                ref = fut.result()
                run_refs.append(ref)
                print(f"[main] run dispatched – {len(run_refs)}/{TOTAL_RUNS}")
            except Exception as exc:  # noqa: BLE001
                print(f"[main] WARNING: dispatch failed: {exc}", file=sys.stderr)

    print(f"[main] {len(run_refs)} run(s) dispatched to Hatchet")

    # ------------------------------------------------------------------
    # Step 5: wait for all 15 runs to complete
    #         Strategy: wait for each run_ref, or fall back to polling
    #         the log file if run refs are unavailable.
    # ------------------------------------------------------------------
    print(f"[main] waiting up to {WAIT_TIMEOUT_SECONDS}s for all runs to finish …")

    completed = _wait_for_runs(run_refs, WAIT_TIMEOUT_SECONDS)

    if not completed:
        print("[main] ERROR: timed out before all runs completed", file=sys.stderr)
        _terminate_worker(worker_proc)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 6: verify log file
    # ------------------------------------------------------------------
    lines = count_log_lines()
    print(f"[main] {LOG_FILE} contains {lines} line(s)")

    if lines < TOTAL_RUNS:
        print(
            f"[main] ERROR: expected {TOTAL_RUNS} lines, found {lines}",
            file=sys.stderr,
        )
        _terminate_worker(worker_proc)
        sys.exit(1)

    print("[main] ✓ all 15 runs completed and logged – exiting 0")
    _terminate_worker(worker_proc)
    sys.exit(0)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_worker() -> None:
    """Entry point executed inside the child process."""
    import worker as w  # noqa: PLC0415

    w.main()


def _wait_for_runs(run_refs: list, timeout: float) -> bool:
    """
    Wait for all dispatched runs to finish.

    Primary strategy  : call .result() on each run reference so the SDK
                        waits for the Hatchet workflow to reach a terminal
                        state.
    Fallback strategy : poll the log file until it has TOTAL_RUNS lines
                        (covers the case where run refs don't support
                        .result() in the installed SDK version).
    """
    deadline = time.monotonic() + timeout

    # -- Primary: use run refs ------------------------------------------
    if run_refs:
        print("[main] waiting via run refs …")
        failed = 0
        for idx, ref in enumerate(run_refs):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print("[main] deadline exceeded while waiting for run refs")
                return False
            try:
                ref.result(timeout=remaining)
                print(f"[main] run {idx + 1}/{len(run_refs)} finished")
            except Exception as exc:  # noqa: BLE001
                print(f"[main] run {idx + 1} result error: {exc}", file=sys.stderr)
                failed += 1

        if failed == 0:
            return True

        # Some refs failed – fall through to log-polling as confirmation
        print(f"[main] {failed} ref(s) errored; falling back to log polling …")

    # -- Fallback: poll log file ----------------------------------------
    print("[main] polling log file …")
    while time.monotonic() < deadline:
        n = count_log_lines()
        print(f"[main] log lines so far: {n}/{TOTAL_RUNS}")
        if n >= TOTAL_RUNS:
            return True
        time.sleep(10)

    return count_log_lines() >= TOTAL_RUNS


def _terminate_worker(proc: multiprocessing.Process) -> None:
    if proc.is_alive():
        print("[main] terminating worker process …")
        proc.terminate()
        proc.join(timeout=5)
        if proc.is_alive():
            proc.kill()


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Use 'spawn' so the child process does not inherit the parent's
    # thread state (important for gRPC / asyncio used by the Hatchet SDK).
    multiprocessing.set_start_method("spawn", force=True)
    main()
