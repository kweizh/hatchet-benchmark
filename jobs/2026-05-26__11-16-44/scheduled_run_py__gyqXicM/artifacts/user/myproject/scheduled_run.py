import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

from hatchet_sdk import Hatchet
from hatchet_sdk.clients.rest.exceptions import NotFoundException
from pydantic import BaseModel

RESULT_PATH = "/tmp/scheduled_result.json"

hatchet = Hatchet()


class ScheduledHelloInput(BaseModel):
    name: str


@hatchet.task(name="scheduled-hello", input_validator=ScheduledHelloInput)
def scheduled_hello(input: ScheduledHelloInput, _context):
    fired_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "fired_at": fired_at,
        "input": input.model_dump(),
    }
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def run_worker() -> None:
    worker = hatchet.worker("scheduled-hello-worker", workflows=[scheduled_hello])
    worker.start()


def main() -> None:
    run_id = str(uuid.uuid4())
    run_at = datetime.now(timezone.utc) + timedelta(seconds=15)

    worker_process = subprocess.Popen(
        [sys.executable, __file__, "worker"],
        env=os.environ.copy(),
    )

    try:
        scheduled_hello.schedule(
            run_at=run_at,
            input=ScheduledHelloInput(name="world"),
            additional_metadata={"run_id": run_id, "source": "scheduled-hello"},
        )

        scheduled_id = None
        for _ in range(10):
            scheduled_list = hatchet.scheduled.list(
                limit=1,
                additional_metadata={"run_id": run_id},
            )
            if scheduled_list.rows:
                scheduled_id = scheduled_list.rows[0].metadata.id
                break
            time.sleep(1)

        time.sleep(30)

        if not scheduled_id:
            raise RuntimeError("Scheduled run not found for cleanup.")

        try:
            hatchet.scheduled.delete(scheduled_id=scheduled_id)
        except NotFoundException:
            pass
    finally:
        worker_process.terminate()
        try:
            worker_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker_process.kill()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        run_worker()
    else:
        main()
