import os
import sys
import time
import datetime
import multiprocessing
import concurrent.futures

from hatchet_sdk import Hatchet, Context, RateLimit, RateLimitDuration

ZEALT_RUN_ID = os.environ.get("ZEALT_RUN_ID", "default")
RATE_LIMIT_KEY = f"ext-api-{ZEALT_RUN_ID}"
LOG_FILE = "/tmp/rate_log.txt"

hatchet = Hatchet(debug=True)

@hatchet.task(
    name="call_external_api",
    rate_limits=[RateLimit(static_key=RATE_LIMIT_KEY, units=1)]
)
def call_external_api(context: Context):
    now = datetime.datetime.now(datetime.timezone.utc)
    # Ensure iso format with Z at the end
    now_str = now.isoformat()
    if now_str.endswith("+00:00"):
        now_str = now_str[:-6] + "Z"
    elif not now_str.endswith("Z"):
        now_str += "Z"
        
    with open(LOG_FILE, "a") as f:
        f.write(now_str + "\n")
    return {"status": "ok"}

def start_worker():
    worker = hatchet.worker("rate-limit-worker", slots=20, workflows=[call_external_api])
    worker.start()

def main():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    hatchet.rate_limits.put(RATE_LIMIT_KEY, 5, RateLimitDuration.MINUTE)

    p = multiprocessing.Process(target=start_worker)
    p.start()

    try:
        time.sleep(3)

        def trigger():
            # If run() is not blocking, this is fast. If it is blocking, threadpool handles it.
            # We can also just use hatchet.admin.run_workflow if this doesn't work, but prompt says:
            # "prefer the SDK helpers such as call_external_api.run_many([...]) or call call_external_api.run() from a thread pool."
            call_external_api.run()

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(trigger) for _ in range(15)]
            # Wait for all runs to be submitted and completed
            concurrent.futures.wait(futures)

        # Ensure we have 15 lines
        start_wait = time.time()
        while True:
            if time.time() - start_wait > 300:
                print("Timeout waiting for 15 runs to complete")
                sys.exit(1)
                
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    lines = [l for l in f.read().splitlines() if l.strip()]
                if len(lines) >= 15:
                    print("15 runs completed")
                    break
                    
            time.sleep(2)
            
    finally:
        p.terminate()
        p.join()
        
    sys.exit(0)

if __name__ == "__main__":
    main()
