import hatchet_sdk
from hatchet_sdk import Hatchet, ConcurrencyExpression, ConcurrencyLimitStrategy
from pydantic import BaseModel

class PaymentInput(BaseModel):
    user_id: str

hatchet = Hatchet()

@hatchet.task(
    name="process_payment_test",
    input_validator=PaymentInput,
    concurrency=ConcurrencyExpression(
        expression="input.user_id",
        max_runs=1,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN
    )
)
def process_payment(context: hatchet_sdk.Context):
    print("running", context.workflow_input())

print("task created successfully")
