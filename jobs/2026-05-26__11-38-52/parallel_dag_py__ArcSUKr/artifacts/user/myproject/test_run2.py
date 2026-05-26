import os
import threading
import time
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()
workflow = hatchet.workflow(name="test-workflow-2")

@workflow.task()
def start(workflow_input, ctx: Context):
    return {"value": 10}

def trigger_workflow():
    time.sleep(2)
    res = workflow.run()
    print("RETURNED:", type(res))
    os._exit(0)

if __name__ == "__main__":
    t = threading.Thread(target=trigger_workflow, daemon=True)
    t.start()
    worker = hatchet.worker("test-worker-2")
    worker.register_workflow(workflow)
    worker.start()
