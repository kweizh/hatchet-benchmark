from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(context: Context):
    input_data = context.workflow_input()
    return {"result": input_data["n"] * 2}

print(double_value)
