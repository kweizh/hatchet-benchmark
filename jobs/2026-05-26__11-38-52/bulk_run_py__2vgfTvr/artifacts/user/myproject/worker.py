import os
from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task(input_validator=InputPayload)
def double_value(input: InputPayload, context: Context):
    return {"result": input.n * 2}

def main():
    worker = hatchet.worker('bulk-worker')
    worker.register_workflow(double_value)
    worker.start()

if __name__ == "__main__":
    main()
