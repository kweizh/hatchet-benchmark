import os
import time
import threading
from hatchet_sdk import Hatchet, Context, Priority
from pydantic import BaseModel

class MyInput(BaseModel):
    priority: int

run_id = os.environ.get("ZEALT_RUN_ID", "default")
task_name = f"prio-task-{run_id}"
log_file = f"/tmp/prio_log_{run_id}.txt"

with open(log_file, "w") as f:
    pass

hatchet = Hatchet()

@hatchet.task(name=task_name, default_priority=Priority.LOW)
def my_task(input: MyInput, ctx: Context):
    prio = input.priority
    epoch_ms = int(time.time() * 1000)
    with open(log_file, "a") as f:
        f.write(f"{prio} {epoch_ms}\n")
    time.sleep(2)
    return {"status": "ok"}

def submit_runs():
    time.sleep(3)
    refs = []
    
    for _ in range(3):
        ref = my_task.run(
            input=MyInput(priority=1),
            priority=Priority.LOW,
            wait_for_result=False
        )
        refs.append(ref)
        
    for _ in range(2):
        ref = my_task.run(
            input=MyInput(priority=3),
            priority=Priority.HIGH,
            wait_for_result=False
        )
        refs.append(ref)
        
    for ref in refs:
        ref.result()
        
    print("All tasks completed.")
    os._exit(0)

def main():
    s_thread = threading.Thread(target=submit_runs, daemon=True)
    s_thread.start()
    
    worker = hatchet.worker("prio-worker", slots=1)
    worker.register_workflow(my_task)
    worker.start()

if __name__ == "__main__":
    main()
