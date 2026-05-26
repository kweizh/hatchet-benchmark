import asyncio
from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload):
    return {"result": input.n * 2}

