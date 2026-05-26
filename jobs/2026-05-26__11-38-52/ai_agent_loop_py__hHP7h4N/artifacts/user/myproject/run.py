import os
import json
import asyncio
import multiprocessing
from datetime import timedelta
from hatchet_sdk import Hatchet, DurableContext

hatchet = Hatchet()

@hatchet.durable_task(name="agent_loop")
async def agent_loop(ctx: DurableContext):
    state_file = "/tmp/agent_state.json"
    
    if not os.path.exists(state_file):
        with open(state_file, "w") as f:
            json.dump({"step": 0, "history": []}, f)
            
    for _ in range(5):
        with open(state_file, "r") as f:
            state = json.load(f)
            
        if state["step"] >= 5:
            break
            
        state["step"] += 1
        state["history"].append({"thought": f"iter {state['step']}"})
        
        with open(state_file, "w") as f:
            json.dump(state, f)
            
        if state["step"] < 5:
            await ctx.aio_sleep_for(timedelta(seconds=1))
        
    with open(state_file, "r") as f:
        state = json.load(f)
        
    return {
        "final_step": state["step"],
        "history_length": len(state["history"])
    }

def run_worker(worker_name):
    worker = hatchet.worker(worker_name)
    worker.register_workflow(agent_loop)
    worker.start()

async def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "default")
    worker_name = f"ai-agent-loop-worker-{run_id}"
    
    for f in ["/tmp/agent_state.json", "/tmp/result.json"]:
        if os.path.exists(f):
            os.remove(f)
            
    # Start worker in a separate process
    p = multiprocessing.Process(target=run_worker, args=(worker_name,), daemon=False)
    p.start()
    
    # Wait a bit for worker to be ready
    await asyncio.sleep(5)
    
    # Trigger task and wait for result
    result = await agent_loop.aio_run({})
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    try:
        # maybe we need to use dict(result) or result.dict() or result.model_dump()
        if hasattr(result, "model_dump"):
            res_dict = result.model_dump()
        elif hasattr(result, "dict"):
            res_dict = result.dict()
        else:
            res_dict = result
            
        with open("/tmp/result.json", "w") as f:
            json.dump(res_dict, f)
    except Exception as e:
        print(f"Error dumping: {e}")
        
    # Terminate the worker process
    p.terminate()
    p.join()

if __name__ == "__main__":
    asyncio.run(main())
