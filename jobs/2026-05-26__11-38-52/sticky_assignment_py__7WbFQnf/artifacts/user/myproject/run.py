import os
import socket
import json
import time
import multiprocessing
import sys
from hatchet_sdk import Hatchet, StickyStrategy

run_id = os.environ.get("ZEALT_RUN_ID", "default")
workflow_name = f"sticky-dag-{run_id}"

def worker_process(worker_id):
    os.environ["WORKER_ID"] = worker_id
    hatchet = Hatchet()
    
    w = hatchet.workflow(name=workflow_name, sticky=StickyStrategy.SOFT)

    @w.task(name="step_a")
    def step_a(input, ctx):
        wid = os.environ.get("WORKER_ID")
        hostname = socket.gethostname()
        pid = os.getpid()
        line = f"step=step_a worker_id={wid} hostname={hostname} pid={pid}\n"
        with open("/tmp/run_steps.log", "a") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return {"worker_id": wid}

    @w.task(name="step_b", parents=[step_a])
    def step_b(input, ctx):
        wid = os.environ.get("WORKER_ID")
        hostname = socket.gethostname()
        pid = os.getpid()
        line = f"step=step_b worker_id={wid} hostname={hostname} pid={pid}\n"
        with open("/tmp/run_steps.log", "a") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return {"worker_id": wid}

    @w.task(name="step_c", parents=[step_b])
    def step_c(input, ctx):
        wid = os.environ.get("WORKER_ID")
        hostname = socket.gethostname()
        pid = os.getpid()
        line = f"step=step_c worker_id={wid} hostname={hostname} pid={pid}\n"
        with open("/tmp/run_steps.log", "a") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return {"worker_id": wid}

    worker = hatchet.worker(worker_id)
    worker.register_workflow(w)
    worker.start()

if __name__ == "__main__":
    if os.path.exists("/tmp/run_steps.log"):
        os.remove("/tmp/run_steps.log")
        
    worker_a_id = f"worker-A-{run_id}"
    worker_b_id = f"worker-B-{run_id}"

    p1 = multiprocessing.Process(target=worker_process, args=(worker_a_id,))
    p2 = multiprocessing.Process(target=worker_process, args=(worker_b_id,))

    p1.start()
    p2.start()

    print("Started workers, waiting for them to be ready...")
    time.sleep(15)

    print("Triggering workflow...")
    hatchet = Hatchet()
    w = hatchet.workflow(name=workflow_name, sticky=StickyStrategy.SOFT)
    w.run(wait_for_result=False)
    
    print("Waiting for workflow to complete...")
    # Poll the log file for 3 lines
    lines = []
    timeout = time.time() + 120
    while time.time() < timeout:
        if os.path.exists("/tmp/run_steps.log"):
            with open("/tmp/run_steps.log", "r") as f:
                lines = f.readlines()
            if len(lines) >= 3:
                break
        time.sleep(1)
    
    print(f"Workflow completed or timed out. Log lines: {len(lines)}")
    
    worker_ids = []
    for line in lines:
        if "worker_id=" in line:
            parts = line.strip().split()
            for p in parts:
                if p.startswith("worker_id="):
                    worker_ids.append(p.split("=")[1])
    
    with open("/tmp/result.json", "w") as f:
        json.dump({"worker_ids": worker_ids}, f)
    
    print("Result written. Terminating workers...")
    p1.terminate()
    p2.terminate()
    p1.join()
    p2.join()
    print("Done.")
