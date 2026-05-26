import os
import json
import time
import threading
from hatchet_sdk import Hatchet

hatchet = Hatchet()
run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
task_name = f"slow_task_{run_id}"

@hatchet.task(name=task_name, execution_timeout="5s", retries=0)
def slow_task(*args, **kwargs):
    time.sleep(20)
    return {"status": "done"}

def trigger_task():
    time.sleep(3)
    try:
        slow_task.run()
        with open("/tmp/result.json", "w") as f:
            json.dump({"timed_out": False}, f)
    except Exception as e:
        with open("/tmp/result.json", "w") as f:
            json.dump({"timed_out": True, "error": str(e)}, f)
    finally:
        os._exit(0)

def main():
    t = threading.Thread(target=trigger_task, daemon=True)
    t.start()
    
    worker = hatchet.worker(f"worker_{run_id}")
    worker.register_workflow(slow_task)
    worker.start()

if __name__ == "__main__":
    main()
