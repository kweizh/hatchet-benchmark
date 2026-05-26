from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task()
def double_value(input: InputPayload):
    return {"result": input.n * 2}

def main():
    items = []
    for i in range(1, 11):
        items.append(double_value.create_bulk_run_item(input=InputPayload(n=i)))

    print("Submitting...")
    # wait, we need a worker to actually run it, otherwise it hangs.
