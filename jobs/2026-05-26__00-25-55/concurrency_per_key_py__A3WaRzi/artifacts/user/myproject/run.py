import asyncio
import os
import subprocess
import time
from hatchet_sdk import Hatchet
from worker import process_payment

async def main():
    # Ensure log file is clean
    log_path = "/tmp/runs.log"
    if os.path.exists(log_path):
        os.remove(log_path)
    
    # Start worker as a background process
    # We use the same environment so ZEALT_RUN_ID and HATCHET_CLIENT_TOKEN are passed
    print("Starting worker...")
    worker_proc = subprocess.Popen(
        ["python3", "worker.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the worker some time to connect to Hatchet Cloud
    print("Waiting for worker to start...")
    await asyncio.sleep(10)
    
    try:
        inputs = [
            {"user_id": "A"},
            {"user_id": "A"},
            {"user_id": "B"},
            {"user_id": "B"},
        ]
        
        print("Triggering 4 runs...")
        # Using asyncio.gather over aio_run as suggested by hints
        tasks = [process_payment.aio_run(input=i) for i in inputs]
        await asyncio.gather(*tasks)
        
        print("All runs finished (according to asyncio.gather).")
        
        # Polling log file as a fallback/verification
        start_time = time.time()
        timeout = 60
        while time.time() - start_time < timeout:
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    lines = f.readlines()
                    if len(lines) == 8:
                        print("Found 8 lines in log.")
                        break
            await asyncio.sleep(1)
        else:
            print("Timed out waiting for 8 lines in log.")
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    print(f"Current log content ({len(f.readlines())} lines):")
                    f.seek(0)
                    print(f.read())

    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        print("Terminating worker...")
        worker_proc.terminate()
        try:
            worker_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
        
        # Print logs for debugging if needed
        stdout, stderr = worker_proc.communicate()
        if stderr:
            print(f"Worker stderr:\n{stderr}")

if __name__ == "__main__":
    asyncio.run(main())
