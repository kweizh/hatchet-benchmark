import json
import os
import sys
import threading
import time
from pathlib import Path

from hatchet_sdk import Hatchet

ATTEMPTS_PATH = Path("/tmp/attempts.txt")
RESULT_PATH = Path("/tmp/result.json")
LOG_PATH = Path("/home/user/myproject/output.log")


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


hatchet = Hatchet()


@hatchet.task(retries=3, backoff_factor=2, backoff_max_seconds=10)
def flaky_task() -> dict:
    attempt = 0
    if ATTEMPTS_PATH.exists():
        try:
            attempt = int(ATTEMPTS_PATH.read_text().strip() or 0)
        except ValueError:
            attempt = 0

    attempt += 1
    ATTEMPTS_PATH.write_text(str(attempt))

    if attempt < 3:
        raise RuntimeError(f"flaky_task failing on attempt {attempt}")

    return {"status": "success", "attempt": attempt}


def main() -> int:
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        raise RuntimeError("ZEALT_RUN_ID environment variable is required")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        sys.stdout = Tee(sys.stdout, log_file)
        sys.stderr = Tee(sys.stderr, log_file)

        if ATTEMPTS_PATH.exists():
            ATTEMPTS_PATH.unlink()

        worker_name = f"task-retries-worker-{run_id}"
        worker = hatchet.worker(worker_name, workflows=[flaky_task])

        worker_thread = threading.Thread(target=worker.start, daemon=True)
        worker_thread.start()

        try:
            time.sleep(1)
            result = flaky_task.run({})
            RESULT_PATH.write_text(json.dumps(result))
        finally:
            worker.shutdown()
            worker_thread.join(timeout=10)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
