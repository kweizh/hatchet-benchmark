import os
import time
import json
import asyncio
import threading
from hatchet_sdk import Hatchet, DurableContext, UserEventCondition, SleepCondition, or_

# Initialize Hatchet
hatchet = Hatchet()

@hatchet.durable_task(name="onboarding_flow")
async def onboarding_flow_task(ctx: DurableContext):
    # As its very first action, it must append the line onboarding_flow started\n to /tmp/events.log
    with open("/tmp/events.log", "a") as f:
        f.write("onboarding_flow started\n")
    
    print("Workflow started, waiting for event or timeout...")
    
    # Call ctx.aio_wait_for(...) with an OR group of two alternatives
    result = await ctx.aio_wait_for(
        or_(
            SleepCondition(duration="30s"),
            UserEventCondition(event_key="user:profile_completed")
        )
    )
    
    print(f"Wait resolved with: {result}")
    
    status = "completed_via_timeout"
    if result and "CREATE" in result:
        if "user:profile_completed" in result["CREATE"]:
            status = "completed_via_event"
    
    return {"status": status}

async def run_worker(worker_name):
    worker = hatchet.worker(worker_name)
    worker.register_task(onboarding_flow_task)
    # Use handle_signals=False to avoid "signal only works in main thread" error
    await worker.start(handle_signals=False)

def start_worker_thread(worker_name, loop):
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_worker(worker_name))
    except Exception as e:
        print(f"Worker error: {e}")

async def main():
    zealt_run_id = os.getenv("ZEALT_RUN_ID", "local-test")
    worker_name = f"event-wait-worker-{zealt_run_id}"
    
    # Start worker in a background thread
    loop = asyncio.new_event_loop()
    worker_thread = threading.Thread(target=start_worker_thread, args=(worker_name, loop), daemon=True)
    worker_thread.start()
    
    # Wait for worker to start
    await asyncio.sleep(5)
    
    print("Triggering task...")
    try:
        run_ref = hatchet.runs.create("onboarding_flow", {})
        # Based on previous output, run_ref has a 'run' attribute which has 'metadata' which has 'id'
        run_id = run_ref.run.metadata.id
        print(f"Task triggered with run_id: {run_id}")
    except Exception as e:
        print(f"Failed to trigger task: {e}")
        # Try to find the run by listing
        await asyncio.sleep(2)
        runs = hatchet.runs.list(workflow_id="onboarding_flow")
        if runs and len(runs) > 0:
            run_id = runs[0].metadata.id
            print(f"Found run_id via list: {run_id}")
        else:
            print("Could not find run_id")
            os._exit(1)
    
    # Approximately 5 seconds after triggering the run, pushes the user:profile_completed event
    await asyncio.sleep(5)
    print("Pushing event...")
    hatchet.event.push("user:profile_completed", {})
    
    # Wait for the run to finish and get result
    print(f"Waiting for run {run_id} to complete...")
    
    result_data = None
    # Use the listener to wait for completion
    try:
        listener = hatchet.listener.stream(run_id)
        async for event in listener:
            print(f"Received event: {event.type}")
            if event.type == "WORKFLOW_RUN_EVENT_FINISHED":
                break
    except Exception as e:
        print(f"Listener error: {e}")
        # Fallback to polling
        await asyncio.sleep(35)
            
    # Try to fetch it via hatchet.runs.get_result
    try:
        # Retry a few times if not immediately available
        for _ in range(5):
            try:
                result_obj = hatchet.runs.get_result(run_id)
                if hasattr(result_obj, "result"):
                    try:
                        result_data = json.loads(result_obj.result)
                    except:
                        result_data = result_obj.result
                else:
                    result_data = result_obj
                if result_data:
                    break
            except:
                await asyncio.sleep(2)
    except Exception as e:
        print(f"Error getting result via API: {e}")
            
    if result_data:
        # Ensure it's the dict we expect
        if isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except:
                pass
        
        with open("/tmp/result.json", "w") as f:
            json.dump(result_data, f)
        print(f"Result written to /tmp/result.json: {result_data}")
    else:
        print("Failed to get result data")

    # Clean shutdown
    print("Shutting down...")
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
