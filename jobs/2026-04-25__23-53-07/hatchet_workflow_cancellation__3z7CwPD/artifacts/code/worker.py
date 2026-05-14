#!/usr/bin/env python3
import time
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

@hatchet.workflow(name="cancellation_workflow", on_events=["cancellation:create"])
class CancellationWorkflow:
    @hatchet.step()
    def check_flag(self, ctx: Context):
        for i in range(10):
            if ctx.exit_flag:
                print("Task has been cancelled")
                raise ValueError("Task has been cancelled")
            
            print(f"Iteration {i}")
            time.sleep(1)
        
        return {"error": "Task should have been cancelled"}

def main():
    worker = hatchet.worker("cancel-worker")
    worker.register_workflow(CancellationWorkflow())
    worker.start()

if __name__ == "__main__":
    main()
