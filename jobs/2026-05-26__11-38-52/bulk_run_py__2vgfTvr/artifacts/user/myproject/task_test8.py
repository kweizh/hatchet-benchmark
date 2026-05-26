from hatchet_sdk import Hatchet
from pydantic import BaseModel
import inspect

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload):
    return {"result": input.n * 2}

print(inspect.signature(double_value.run_many))
