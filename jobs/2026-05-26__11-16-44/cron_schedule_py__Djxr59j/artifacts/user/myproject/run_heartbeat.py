import os
import sys
import time
import threading
from datetime import datetime, timezone

from hatchet_sdk import Hatchet

OUTPUT_LOG_PATH = "/home/user/myproject/output.log"
HEARTBEAT_PATH = "/tmp/heartbeats.log"


def _redirect_output():
    log_file = open(OUTPUT_LOG_PATH, "a", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    return log_file


def _write_heartbeat():
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(HEARTBEAT_PATH, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\n")


def _extract_cron_id(response):
    if response is None:
        return None
    if isinstance(response, dict):
        return response.get("id") or response.get("cron_id")
    return getattr(response, "id", None) or getattr(response, "cron_id", None)


def _create_cron(task_handle, hatchet, cron_name, expression):
    if hasattr(task_handle, "cron"):
        try:
            return task_handle.cron(name=cron_name, cron=expression, input={})
        except TypeError:
            return task_handle.cron(name=cron_name, schedule=expression, input={})
    if hasattr(task_handle, "create_cron"):
        try:
            return task_handle.create_cron(name=cron_name, cron=expression, input={})
        except TypeError:
            return task_handle.create_cron(name=cron_name, schedule=expression, input={})
    cron_api = getattr(hatchet, "cron", None)
    if cron_api and hasattr(cron_api, "create"):
        try:
            return cron_api.create(name=cron_name, cron=expression, task_name=task_handle.name, input={})
        except TypeError:
            return cron_api.create(name=cron_name, schedule=expression, task_name=task_handle.name, input={})
    raise RuntimeError("Unable to create cron via Hatchet SDK; API method not found")


def _delete_cron(hatchet, cron_id):
    if cron_id is None:
        return
    cron_api = getattr(hatchet, "cron", None)
    if cron_api and hasattr(cron_api, "delete"):
        cron_api.delete(cron_id)
        return
    if hasattr(hatchet, "delete_cron"):
        hatchet.delete_cron(cron_id)
        return
    raise RuntimeError("Unable to delete cron via Hatchet SDK; API method not found")


def _run_worker(worker):
    if hasattr(worker, "run"):
        worker.run()
        return
    if hasattr(worker, "start"):
        worker.start()
        return
    raise RuntimeError("Worker start method not found")


def _stop_worker(worker):
    for method_name in ("shutdown", "stop", "close"):
        method = getattr(worker, method_name, None)
        if method:
            method()
            return


def main():
    log_file = _redirect_output()
    worker = None
    worker_thread = None
    hatchet = None
    cron_id = None
    try:
        run_id = os.environ["ZEALT_RUN_ID"]
        hatchet = Hatchet()

        task_name = f"heartbeat-{run_id}"
        cron_name = f"hb-cron-{run_id}"

        @hatchet.task(name=task_name)
        def heartbeat(_context):
            _write_heartbeat()

        worker = hatchet.worker("heartbeat-worker", tasks=[heartbeat])
        worker_thread = threading.Thread(target=_run_worker, args=(worker,), daemon=True)
        worker_thread.start()

        time.sleep(2)

        cron_response = _create_cron(heartbeat, hatchet, cron_name, "* * * * *")
        cron_id = _extract_cron_id(cron_response)

        time.sleep(75)
    finally:
        if worker is not None:
            _stop_worker(worker)
        if worker_thread is not None:
            worker_thread.join(timeout=10)
        if hatchet is not None:
            _delete_cron(hatchet, cron_id)
        log_file.close()


if __name__ == "__main__":
    main()
