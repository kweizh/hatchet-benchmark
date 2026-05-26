import os
import sys
import time
import threading
from datetime import datetime, timezone
from hatchet_sdk import Hatchet

hatchet = Hatchet()

@hatchet.task(name="heartbeat")
def heartbeat(*args, **kwargs):
    timestamp = datetime.now(timezone.utc).isoformat()
    with open("/tmp/heartbeats.log", "a") as f:
        f.write(timestamp + "\n")
    print(f"Heartbeat logged: {timestamp}")

def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "default")
    cron_name = f"hb-cron-{run_id}"
    
    worker = hatchet.worker("heartbeat-worker")
    worker.register_workflow(heartbeat)

    def run_worker():
        worker.start()

    t = threading.Thread(target=run_worker)
    t.daemon = True
    t.start()
    
    # Wait for the worker to register the workflow
    time.sleep(5)

    # Create cron trigger
    try:
        res = hatchet.cron.create(
            workflow_name="heartbeat",
            cron_name=cron_name,
            expression="* * * * *",
            input={},
            additional_metadata={}
        )
        cron_id = res.metadata.id
        print(f"Created cron trigger {cron_name} with id {cron_id}")
    except Exception as e:
        print(f"Error creating cron trigger: {e}")
        sys.exit(1)

    # Wait for 75 seconds to ensure at least one cron firing
    print("Waiting 75 seconds for cron to fire...")
    time.sleep(75)

    # Delete cron trigger
    print(f"Deleting cron trigger {cron_id}")
    try:
        hatchet.cron.delete(cron_id)
        print("Cron trigger deleted successfully.")
    except Exception as e:
        print(f"Error deleting cron trigger: {e}")

    # Shut down worker cleanly
    print("Exiting...")
    sys.exit(0)

if __name__ == '__main__':
    main()
