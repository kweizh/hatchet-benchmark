from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class DoubleInput(BaseModel):
    n: int

class DoubleOutput(BaseModel):
    result: int

@hatchet.task(input_validator=DoubleInput)
def double_value(input: DoubleInput, ctx: Context) -> DoubleOutput:
    return DoubleOutput(result=input.n * 2)
