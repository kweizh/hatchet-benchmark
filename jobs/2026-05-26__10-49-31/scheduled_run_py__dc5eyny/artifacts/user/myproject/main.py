"""
Hatchet Scheduled Run Demo
--------------------------
1. Starts worker.py as a subprocess (worker must run in its own main thread).
2. Defines / reuses the `scheduled-hello` task registration to schedule a run.
3. Schedules the task to fire once at now + 15 seconds with input {"name": "world"}.
4. Waits 35 seconds for the scheduled time to pass and the task to execute.
5. Deletes (cleans up) the scheduled run via the SDK.
6. Verifies /tmp/scheduled_result.json was written by the task.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

from hatchet_sdk import Hatchet

# ---------------------------------------------------------------------------
# Hatchet client (reads HATCHET_CLIENT_TOKEN from env automatically)
# ---------------------------------------------------------------------------
hatchet = Hatchet()


def main() -> None:
    # 1. Start the worker subprocess so it can pick up the scheduled run.
    #    The worker registers the `scheduled-hello` task and listens for work.
    print("[main] starting worker subprocess …", flush=True)
    worker_proc = subprocess.Popen(
        [sys.executable, "worker.py"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # Give the worker a moment to connect and register.
    time.sleep(5)

    try:
        # 2. Schedule the task ~15 s in the future
        trigger_at = datetime.now(tz=timezone.utc) + timedelta(seconds=15)
        print(
            f"[main] scheduling 'scheduled-hello' to fire at {trigger_at.isoformat()} …",
            flush=True,
        )

        schedule = hatchet.scheduled.create(
            workflow_name="scheduled-hello",
            trigger_at=trigger_at,
            input={"name": "world"},
            additional_metadata={},
        )
        scheduled_id = schedule.metadata.id
        print(f"[main] scheduled run created, id={scheduled_id}", flush=True)

        # 3. Wait long enough for the scheduled time + task execution time.
        wait_seconds = 35
        print(
            f"[main] waiting {wait_seconds}s for the scheduled run to execute …",
            flush=True,
        )
        time.sleep(wait_seconds)

        # 4. Verify result file was written by the task.
        result_path = "/tmp/scheduled_result.json"
        try:
            with open(result_path) as fh:
                result = json.load(fh)
            print(f"[main] ✓ result file contents: {result}", flush=True)
        except FileNotFoundError:
            print(
                f"[main] WARNING: result file {result_path} not found – task may not have run yet.",
                flush=True,
            )

        # 5. Clean up the scheduled run.
        print(f"[main] deleting scheduled run {scheduled_id} …", flush=True)
        try:
            hatchet.scheduled.delete(scheduled_id=scheduled_id)
            print("[main] ✓ scheduled run deleted successfully", flush=True)
        except Exception as exc:
            # The run may have already been consumed / auto-deleted by the server.
            print(f"[main] cleanup note: {exc}", flush=True)

    finally:
        # Terminate the worker subprocess.
        print("[main] stopping worker subprocess …", flush=True)
        worker_proc.terminate()
        try:
            worker_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker_proc.kill()

    print("[main] done", flush=True)


if __name__ == "__main__":
    main()
