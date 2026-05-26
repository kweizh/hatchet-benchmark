import os
import time
import json
from datetime import datetime, timezone
from multiprocessing import Process
from hatchet_sdk import Hatchet, RateLimit, RateLimitDuration, Context

# Initialize Hatchet client
hatchet = Hatchet()

# Read ZEALT_RUN_ID and build the rate limit key
zealt_run_id = os.getenv("ZEALT_RUN_ID")
if not zealt_run_id:
    raise ValueError("ZEALT_RUN_ID environment variable is not set")

rate_limit_key = f"ext-api-{zealt_run_id}"
log_file = "/tmp/rate_log.txt"

@hatchet.task(
    name="call_external_api",
    rate_limits=[RateLimit(static_key=rate_limit_key, units=1)]
)
def call_external_api(workflow_input: dict, context: Context):
    # Get current UTC time in ISO 8601 format with trailing Z
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Append to log file (thread-safe/process-safe for single write call)
    with open(log_file, "a") as f:
        f.write(f"{timestamp}\n")
    
    return {"status": "success", "timestamp": timestamp}

def run_worker():
    # call_external_api is a Standalone task object
    worker = hatchet.worker("rate-limit-worker", slots=20, workflows=[call_external_api])
    worker.start()

def main():
    # 1. Clear pre-existing log file
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # 2. Register/update the static rate limit
    print(f"Registering rate limit: {rate_limit_key} (5 per minute)")
    hatchet.rate_limits.put(rate_limit_key, 5, RateLimitDuration.MINUTE)
    
    # 3. Start Hatchet worker in a background process
    worker_process = Process(target=run_worker)
    worker_process.start()
    
    try:
        # Give worker a moment to start
        time.sleep(10)
        
        # 4. Trigger 15 runs of call_external_api in parallel
        print("Triggering 15 runs...")
        for i in range(15):
            # Using call_external_api.run() which handles the input correctly
            # We don't want to wait for it here, but we want it to be dispatched
            # Actually call_external_api.run() is blocking.
            # We should use hatchet.event.push_event or similar if we want async.
            # But the requirement says "trigger 15 runs in parallel (or in very rapid succession)".
            # Let's use threads to trigger them in parallel.
            pass
        
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=15) as executor:
            for i in range(15):
                executor.submit(call_external_api.run, {})

        # 5. Wait until all 15 runs have completed
        print("Waiting for runs to complete (up to 5 minutes)...")
        start_time = time.time()
        while time.time() - start_time < 300:
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    lines = [line.strip() for line in f if line.strip()]
                
                print(f"Progress: {len(lines)}/15 runs completed")
                if len(lines) >= 15:
                    print("All runs completed!")
                    break
            time.sleep(10)
        else:
            print("Timed out waiting for runs to complete.")
            
    finally:
        # 6. Terminate the worker
        print("Terminating worker...")
        worker_process.terminate()
        worker_process.join()

if __name__ == "__main__":
    main()
