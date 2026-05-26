import os
import json
import asyncio
from datetime import timedelta
from hatchet_sdk import Hatchet, DurableContext

# Initialize Hatchet client
hatchet = Hatchet()

STATE_FILE = "/tmp/agent_state.json"
RESULT_FILE = "/tmp/result.json"

@hatchet.durable_task()
async def agent_loop(ctx: DurableContext):
    # On the very first iteration, initialize the state file if it does not exist
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'w') as f:
            json.dump({"step": 0, "history": []}, f)

    while True:
        # 1. Read the current state
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)

        step = state.get("step", 0)
        history = state.get("history", [])

        # Exit the loop as soon as step == 5
        if step >= 5:
            break

        # 2. Increment step by 1
        step += 1
        
        # 3. Append thought
        history.append({"thought": f"iter {step}"})

        # 4. Write the updated state
        state["step"] = step
        state["history"] = history
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)

        # 5. Yield back to Hatchet via durable sleep
        # Exit check again before sleep to avoid extra sleep if we just hit 5
        if step == 5:
            break
            
        await ctx.aio_sleep_for(timedelta(seconds=1))

    return {"final_step": 5, "history_length": 5}

async def main():
    zealt_run_id = os.getenv("ZEALT_RUN_ID", "local")
    worker_name = f"ai-agent-loop-worker-{zealt_run_id}"

    # Remove pre-existing files
    for f in [STATE_FILE, RESULT_FILE]:
        if os.path.exists(f):
            os.remove(f)

    # Create worker
    worker = hatchet.worker(worker_name)
    worker.register_workflow(agent_loop)

    # Start worker in a background task
    worker_task = asyncio.create_task(asyncio.to_thread(worker.start))

    try:
        # Wait a bit for worker to be ready (though hatchet.admin.run should handle it)
        await asyncio.sleep(2)

        # Trigger run
        print(f"Triggering agent_loop run for worker {worker_name}...")
        workflow_run = agent_loop.run({})
        
        # Wait for result
        print("Waiting for workflow run to complete...")
        result = workflow_run.result()
        print(f"Run completed with result: {result}")

        # Write result file
        with open(RESULT_FILE, 'w') as f:
            json.dump(result, f)

    finally:
        # Shutdown worker
        print("Stopping worker...")
        # worker.stop() # If stop doesn't exist, we might just let main exit
        if hasattr(worker, 'stop'):
            worker.stop()
        await worker_task

if __name__ == "__main__":
    asyncio.run(main())
