from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel
import inspect

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task(input_validator=InputPayload)
def double_value(context: Context):
    pass

print(inspect.signature(double_value.run_many))
