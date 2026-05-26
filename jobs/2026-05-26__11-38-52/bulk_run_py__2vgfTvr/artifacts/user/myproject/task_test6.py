from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload):
    return {"result": input.n * 2}

items = []
for i in range(1, 11):
    items.append(double_value.create_bulk_run_item(input={"n": i}))

print(type(items[0]))
