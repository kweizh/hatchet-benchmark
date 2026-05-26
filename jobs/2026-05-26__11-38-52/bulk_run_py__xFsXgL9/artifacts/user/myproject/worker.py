from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class DoubleInput(BaseModel):
    n: int

@hatchet.task(input_validator=DoubleInput)
def double_value(input_data: DoubleInput, context: Context):
    return {"result": input_data.n * 2}

if __name__ == "__main__":
    worker = hatchet.worker("my-worker")
    worker.register_workflow(double_value)
    worker.start()
