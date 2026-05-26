from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload, context: Context):
    return {"result": input.n * 2}

print(double_value.input_validator_type)
