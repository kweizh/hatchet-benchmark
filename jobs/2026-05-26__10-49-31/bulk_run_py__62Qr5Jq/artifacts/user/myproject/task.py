from pydantic import BaseModel
from hatchet_sdk import Context, Hatchet

hatchet = Hatchet()


class DoubleInput(BaseModel):
    n: int


class DoubleOutput(BaseModel):
    result: int


@hatchet.task(name="double-value", input_validator=DoubleInput)
def double_value(input: DoubleInput, ctx: Context) -> DoubleOutput:
    return DoubleOutput(result=input.n * 2)
