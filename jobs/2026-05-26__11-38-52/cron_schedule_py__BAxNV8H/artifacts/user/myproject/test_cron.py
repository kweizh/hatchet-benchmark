import os
import time
import threading
from hatchet_sdk import Hatchet
hatchet = Hatchet()
@hatchet.task(name="heartbeat")
def heartbeat(context):
    print("Heartbeat task executed")

def main():
    worker = hatchet.worker("test-worker")
    worker.register_workflow(heartbeat)

    def run_worker():
        worker.start()

    t = threading.Thread(target=run_worker)
    t.daemon = True
    t.start()
    time.sleep(2) # wait for worker to register the workflow

    res = hatchet.cron.create(
        workflow_name="heartbeat",
        cron_name="test-cron",
        expression="* * * * *",
        input={},
        additional_metadata={}
    )
    print(res.metadata.id)
    hatchet.cron.delete(res.metadata.id)

if __name__ == '__main__':
    main()
