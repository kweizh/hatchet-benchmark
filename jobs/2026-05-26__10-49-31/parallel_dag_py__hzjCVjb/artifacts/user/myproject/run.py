"""Trigger a single diamond-dag workflow run and persist the merge output."""
import json
import subprocess
import sys
import time

from diamond_workflow import workflow

if __name__ == "__main__":
    # Start the worker as a subprocess (avoids signal-handler restriction)
    worker_proc = subprocess.Popen(
        [sys.executable, "worker.py"],
        cwd="/home/user/myproject",
    )

    try:
        # Give the worker time to connect and register with Hatchet Cloud
        print("Waiting for worker to come online...")
        time.sleep(5)

        print("Triggering workflow run...")
        result = workflow.run()

        print(f"Workflow completed. Full result: {result}")

        # result is a dict keyed by task name; grab the merge task output
        merge_output = result.get("merge", result)

        with open("/tmp/result.json", "w") as f:
            json.dump(merge_output, f, indent=2)

        print(f"Written to /tmp/result.json: {merge_output}")
    finally:
        worker_proc.terminate()
        worker_proc.wait()
