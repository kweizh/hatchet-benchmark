import json
import os
import threading
import time

from hatchet_sdk import Hatchet

RUN_ID = os.getenv("ZEALT_RUN_ID", "local")
TASK_NAME = f"slow_task_{RUN_ID}"

hatchet = Hatchet()


@hatchet.task(name=TASK_NAME, execution_timeout="5s", retries=0)
def slow_task(context):
    time.sleep(20)
    return {"status": "done"}


def start_worker():
    worker = hatchet.worker()
    thread = threading.Thread(target=worker.start, daemon=True)
    thread.start()
    return worker, thread


def stop_worker(worker):
    for method_name in ("stop", "shutdown", "close"):
        method = getattr(worker, method_name, None)
        if callable(method):
            try:
                method()
            except Exception:
                pass
            break


def write_result(payload):
    with open("/tmp/result.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def main():
    worker, _thread = start_worker()
    time.sleep(1)

    try:
        slow_task.run()
        result = {"timed_out": False}
    except Exception as exc:
        result = {"timed_out": True, "error": str(exc)}

    write_result(result)
    stop_worker(worker)


if __name__ == "__main__":
    main()
