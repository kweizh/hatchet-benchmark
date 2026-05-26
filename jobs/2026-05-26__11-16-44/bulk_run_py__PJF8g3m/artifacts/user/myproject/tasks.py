from pydantic import BaseModel
from hatchet_sdk import Context, Hatchet

hatchet = Hatchet()


class DoubleValueInput(BaseModel):
    n: int


class DoubleValueOutput(BaseModel):
    result: int


@hatchet.task(name="double_value", input_validator=DoubleValueInput)
def double_value(input: DoubleValueInput, ctx: Context) -> DoubleValueOutput:
    return DoubleValueOutput(result=input.n * 2)
