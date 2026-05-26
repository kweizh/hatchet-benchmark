import json
import os
import sys
import threading
import time
from datetime import timedelta
from typing import Any, Dict

from hatchet_sdk import DurableContext, Hatchet

STATE_PATH = "/tmp/agent_state.json"
RESULT_PATH = "/tmp/result.json"
LOG_PATH = "/home/user/myproject/output.log"

hatchet = Hatchet()


class TeeWriter:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def _load_state() -> Dict[str, Any]:
    with open(STATE_PATH, "r", encoding="utf-8") as state_file:
        return json.load(state_file)


def _write_state(state: Dict[str, Any]) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as state_file:
        json.dump(state, state_file)


@hatchet.durable_task(name="agent_loop")
async def agent_loop(_: dict, ctx: DurableContext) -> Dict[str, int]:
    if not os.path.exists(STATE_PATH):
        _write_state({"step": 0, "history": []})

    for _ in range(5):
        state = _load_state()
        step = int(state.get("step", 0)) + 1
        history = list(state.get("history", []))
        history.append({"thought": f"iter {step}"})
        updated_state = {"step": step, "history": history}
        _write_state(updated_state)

        await ctx.aio_sleep_for(timedelta(seconds=1))

        if step >= 5:
            break

    return {"final_step": 5, "history_length": 5}


def _cleanup_files() -> None:
    for path in (STATE_PATH, RESULT_PATH):
        if os.path.exists(path):
            os.remove(path)


def _start_worker(worker) -> threading.Thread:
    thread = threading.Thread(target=worker.start, daemon=True)
    thread.start()
    return thread


def _stop_worker(worker) -> None:
    for method_name in ("stop", "shutdown", "close"):
        method = getattr(worker, method_name, None)
        if callable(method):
            method()
            break


def main() -> int:
    zealt_run_id = os.environ.get("ZEALT_RUN_ID")
    if not zealt_run_id:
        raise RuntimeError("ZEALT_RUN_ID is not set")

    _cleanup_files()

    worker = hatchet.worker(
        name=f"ai-agent-loop-worker-{zealt_run_id}",
        workflows=[agent_loop],
    )
    worker_thread = _start_worker(worker)

    time.sleep(1)

    try:
        result = agent_loop.run({})
        with open(RESULT_PATH, "w", encoding="utf-8") as result_file:
            json.dump(result, result_file)
    finally:
        _stop_worker(worker)
        worker_thread.join(timeout=10)

    return 0


if __name__ == "__main__":
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        sys.stdout = TeeWriter(sys.stdout, log_file)
        sys.stderr = TeeWriter(sys.stderr, log_file)
        raise SystemExit(main())
