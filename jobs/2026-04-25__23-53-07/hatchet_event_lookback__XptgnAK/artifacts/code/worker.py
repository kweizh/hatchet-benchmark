from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel
from datetime import timedelta

hatchet = Hatchet()

class UserInput(BaseModel):
    user_id: str

@hatchet.workflow(on_events=["user:process"])
class ProcessUser:
    @hatchet.step()
    async def wait_for_user(self, ctx: Context):
        # Parse input into the Pydantic model
        user_input = UserInput(**ctx.workflow_input())
        user_id = user_input.user_id
        
        # Wait for the 'user:create' event
        # expression: CEL expression to match the user_id from the event payload
        # scope: restricts the search space for the event
        # lookback: allows catching events that occurred up to 5 minutes before the wait started
        event = await ctx.aio_wait_for_event(
            key="user:create",
            expression=f"event.user_id == '{user_id}'",
            scope=f"user_id:{user_id}",
            lookback=timedelta(minutes=5)
        )
        
        return event.payload

if __name__ == "__main__":
    worker = hatchet.worker("user-worker")
    worker.register_workflow(ProcessUser())
    worker.start()
