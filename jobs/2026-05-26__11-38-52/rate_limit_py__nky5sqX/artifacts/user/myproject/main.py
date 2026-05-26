import os
import sys
import time
import datetime
import multiprocessing
from hatchet_sdk import Hatchet, Context, RateLimit, RateLimitDuration

run_id = os.environ.get("ZEALT_RUN_ID", "default")
rate_limit_key = f"ext-api-{run_id}"

hatchet = Hatchet(debug=True)

@hatchet.task(
    name="call_external_api",
    rate_limits=[RateLimit(static_key=rate_limit_key, units=1)]
)
def call_external_api(context: Context):
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_str = now.isoformat(timespec='microseconds').replace("+00:00", "Z")
    if not timestamp_str.endswith("Z"):
        timestamp_str += "Z"
        
    with open("/tmp/rate_log.txt", "a") as f:
        f.write(timestamp_str + "\n")
    return "done"

def run_worker():
    worker = hatchet.worker("rate-limit-worker", slots=20, workflows=[call_external_api])
    worker.start()

def main():
    log_file = "/tmp/rate_log.txt"
    if os.path.exists(log_file):
        os.remove(log_file)
        
    print(f"Registering static rate limit: {rate_limit_key}")
    hatchet.rate_limits.put(rate_limit_key, 5, RateLimitDuration.MINUTE)
    
    p = multiprocessing.Process(target=run_worker)
    p.start()
    
    time.sleep(5)  # Wait for worker to start
    
    print("Triggering 15 runs...")
    
    for _ in range(15):
        call_external_api.run(wait_for_result=False)
            
    print("Runs triggered. Waiting for completion...")
    
    start_wait = time.time()
    while True:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.read().strip().split("\n")
                lines = [l for l in lines if l]
                print(f"Current completed runs: {len(lines)}")
                if len(lines) >= 15:
                    print("All 15 runs completed!")
                    break
        if time.time() - start_wait > 300:
            print("Timeout waiting for runs")
            p.terminate()
            sys.exit(1)
        time.sleep(5)
        
    p.terminate()
    p.join()
    sys.exit(0)

if __name__ == "__main__":
    main()
