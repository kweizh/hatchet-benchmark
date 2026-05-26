"""
Worker process for the scheduled-hello task.
Run this as a separate process so signal handlers work in the main thread.
"""

import json
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from hatchet_sdk import Context, Hatchet

hatchet = Hatchet()


class HelloInput(BaseModel):
    name: str = ""


@hatchet.task(
    name="scheduled-hello",
    input_validator=HelloInput,
    execution_timeout=timedelta(seconds=60),
)
def scheduled_hello(input: HelloInput, ctx: Context) -> dict:
    """Write a result file and return the payload."""
    fired_at = datetime.now(tz=timezone.utc).isoformat()

    # Use the raw workflow input dict from ctx to preserve all keys faithfully.
    raw_input: dict = ctx._workflow_input  # type: ignore[attr-defined]

    payload = {
        "fired_at": fired_at,
        "input": raw_input,
    }

    result_path = "/tmp/scheduled_result.json"
    with open(result_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"[scheduled-hello] wrote result to {result_path}: {payload}", flush=True)
    return payload


if __name__ == "__main__":
    worker = hatchet.worker(
        name="scheduled-hello-worker",
        workflows=[scheduled_hello],
    )
    print("[worker] starting …", flush=True)
    worker.start()
