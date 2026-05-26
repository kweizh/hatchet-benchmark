import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

from hatchet_sdk import Hatchet

OUTPUT_PATH = "/tmp/triggered.json"
EVENT_KEY = "user:created"
TASK_NAME = "on_user_created"
WORKER_NAME = "on-user-created-worker"


hatchet = Hatchet()


@hatchet.task(name=TASK_NAME, on_events=[EVENT_KEY])
def on_user_created(payload: Any) -> None:
    if hasattr(payload, "model_dump"):
        event_payload = payload.model_dump()
    elif isinstance(payload, dict):
        event_payload = payload
    else:
        event_payload = dict(payload)

    record = {
        "event_payload": event_payload,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(record, handle)


def _start_worker() -> None:
    worker = hatchet.worker(WORKER_NAME, workflows=[on_user_created])
    worker.start()


def _wait_for_trigger(timeout_seconds: int = 60) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if os.path.exists(OUTPUT_PATH):
            return True
        time.sleep(1)
    return False


def main() -> None:
    if os.getenv("HATCHET_CLIENT_TOKEN") is None:
        raise RuntimeError("HATCHET_CLIENT_TOKEN must be set for Hatchet Cloud")

    run_id = os.getenv("ZEALT_RUN_ID")
    if not run_id:
        raise RuntimeError("ZEALT_RUN_ID must be set")

    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)

    worker_thread = threading.Thread(target=_start_worker, daemon=True)
    worker_thread.start()

    time.sleep(5)

    hatchet.event.push(EVENT_KEY, {"user_id": f"abc-{run_id}"})

    if not _wait_for_trigger(timeout_seconds=60):
        raise TimeoutError("Timed out waiting for event trigger")


if __name__ == "__main__":
    main()
