from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload):
    return {"n": input.n, "result": input.n * 2}

worker = hatchet.worker('test')
worker.register_workflow(double_value)
print("Registered!")
