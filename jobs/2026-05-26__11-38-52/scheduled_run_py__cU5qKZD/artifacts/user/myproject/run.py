import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone, timedelta
from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

class MyInput(BaseModel):
    name: str

hatchet = Hatchet()

@hatchet.task(name="scheduled-hello")
def hello(workflow_input: MyInput, context: Context):
    data = {
        "fired_at": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "input": workflow_input.model_dump()
    }
    with open("/tmp/scheduled_result.json", "w") as f:
        json.dump(data, f)
    print("Task fired!", data)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        worker = hatchet.worker("test-worker")
        worker.register_workflow(hello)
        worker.start()
    else:
        print("Starting worker process...")
        proc = subprocess.Popen([sys.executable, __file__, "worker"])
        
        try:
            # Wait a moment for worker to connect
            time.sleep(3)
            
            print("Scheduling task...")
            # Schedule task 15 seconds in the future
            sched = hello.schedule(
                run_at=datetime.now(tz=timezone.utc) + timedelta(seconds=15),
                input={"name": "world"}
            )
            
            # The equivalent attribute exposed by the SDK for the schedule id
            sched_id = sched.scheduled_workflows[0].id
            print(f"Scheduled ID: {sched_id}")
            
            # Wait for the task to execute (at least ~30 seconds total)
            print("Waiting for 30 seconds for task to execute...")
            time.sleep(30)
            
            print("Cleaning up schedule...")
            try:
                hatchet.scheduled.delete(scheduled_id=sched_id)
                print("Deleted schedule.")
            except Exception as e:
                print("Schedule was likely already consumed and deleted automatically.")
                print(f"Delete error: {e}")
                
        finally:
            print("Terminating worker...")
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    main()
