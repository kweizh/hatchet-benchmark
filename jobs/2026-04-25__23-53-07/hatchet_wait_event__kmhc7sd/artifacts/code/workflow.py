from hatchet_sdk import Hatchet, DurableContext, UserEventCondition, SleepCondition, or_
from datetime import timedelta

hatchet = Hatchet()

# Define the workflow
workflow = hatchet.workflow(name="OrderWorkflow")

@workflow.durable_task()
async def process_order(ctx: DurableContext):
    # Wait for either user confirmation or a 5-minute timeout
    # We use readable_data_key to easily identify which condition was met
    result = await ctx.aio_wait_for(
        "order-wait",
        or_(
            UserEventCondition(event_key="user:confirm", readable_data_key="confirm"),
            SleepCondition(timedelta(minutes=5), readable_data_key="timeout")
        )
    )

    # The result contains a "CREATE" key with the triggered conditions
    triggered_conditions = result.get("CREATE", {})
    
    # If the "confirm" condition was met
    if "confirm" in triggered_conditions:
        return {"status": "confirmed"}
    
    # Otherwise (timeout or other condition)
    return {"status": "cancelled"}
