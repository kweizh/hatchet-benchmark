import os
import sys
import time
import threading
from datetime import datetime, timezone

from hatchet import Hatchet, RateLimit, RateLimitDuration

LOG_PATH = "/tmp/rate_log.txt"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    run_id = os.getenv("ZEALT_RUN_ID")
    if not run_id:
        print("ZEALT_RUN_ID is not set", file=sys.stderr)
        return 1

    rate_key = f"ext-api-{run_id}"

    try:
        if os.path.exists(LOG_PATH):
            os.remove(LOG_PATH)
    except OSError as exc:
        print(f"Failed to clear {LOG_PATH}: {exc}", file=sys.stderr)
        return 1

    hatchet = Hatchet(debug=True)
    hatchet.rate_limits.put(rate_key, 5, RateLimitDuration.MINUTE)

    @hatchet.task(
        name="call_external_api",
        rate_limits=[RateLimit(static_key=rate_key, units=1)],
    )
    def call_external_api() -> None:
        timestamp = utc_timestamp()
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(f"{timestamp}\n")

    worker = hatchet.worker(
        "rate-limit-worker",
        slots=20,
        workflows=[call_external_api],
    )

    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()

    runs = []
    for _ in range(15):
        runs.append(call_external_api.run())

    deadline = time.time() + 300
    for run in runs:
        remaining = max(0, deadline - time.time())
        run.wait(timeout=remaining)

    for _ in range(300):
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as handle:
                lines = [line.strip() for line in handle.readlines() if line.strip()]
            if len(lines) == 15:
                break
        time.sleep(1)
    else:
        print("Timed out waiting for 15 log lines", file=sys.stderr)
        return 1

    worker.stop()
    worker_thread.join(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
