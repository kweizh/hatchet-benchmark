import json
from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel

hatchet = Hatchet()

class InputPayload(BaseModel):
    n: int

@hatchet.task(input_validator=InputPayload)
def double_value(input: InputPayload, context: Context):
    return {"result": input.n * 2}

def main():
    items = []
    for i in range(1, 11):
        items.append(double_value.create_bulk_run_item(input=InputPayload(n=i)))
    
    print("Submitting bulk run...")
    results = double_value.run_many(items)
    
    output = []
    for i, res in enumerate(results):
        n = i + 1
        if isinstance(res, dict):
            val = res["result"]
        else:
            val = getattr(res, "result", None)
            
        output.append({"n": n, "result": val})
        
    with open("/tmp/results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Wrote results to /tmp/results.json")

if __name__ == "__main__":
    main()
