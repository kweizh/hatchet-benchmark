from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload):
    return {"result": input.n * 2}

print(dir(double_value))
print(hasattr(double_value, 'run_many'))
print(hasattr(double_value, 'create_bulk_run_item'))
