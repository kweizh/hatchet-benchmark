import atexit
import json
import os
import sys
import threading
import time

from hatchet_sdk import Context, Hatchet

LOG_PATH = "/home/user/myproject/output.log"
RESULT_PATH = "/tmp/result.json"


def redirect_output() -> None:
    log_file = open(LOG_PATH, "a", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    atexit.register(log_file.close)


def stop_worker(worker: object) -> None:
    for method_name in ("shutdown", "stop", "close"):
        method = getattr(worker, method_name, None)
        if callable(method):
            try:
                result = method()
                if hasattr(result, "__await__"):
                    import asyncio

                    asyncio.run(result)
            except Exception:
                pass
            return


def main() -> None:
    redirect_output()

    zealt_run_id = os.environ.get("ZEALT_RUN_ID")
    if not zealt_run_id:
        raise RuntimeError("ZEALT_RUN_ID is not set")

    hatchet = Hatchet()

    @hatchet.task(name="simple_greeting")
    def simple_greeting(input_data: dict, ctx: Context) -> dict:
        name = input_data["name"]
        return {"greeting": f"Hello, {name}!"}

    worker_name = f"basic-task-worker-{zealt_run_id}"
    worker = hatchet.worker(worker_name, workflows=[simple_greeting])

    worker_thread = threading.Thread(target=worker.start, name="hatchet-worker", daemon=True)
    worker_thread.start()

    time.sleep(1)
    result = simple_greeting.run({"name": "World"})

    with open(RESULT_PATH, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file)

    stop_worker(worker)
    worker_thread.join(timeout=5)


if __name__ == "__main__":
    main()
