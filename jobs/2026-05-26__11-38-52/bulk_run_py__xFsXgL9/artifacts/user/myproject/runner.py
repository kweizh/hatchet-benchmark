import json
from hatchet_sdk import Hatchet
from worker import double_value, DoubleInput

hatchet = Hatchet()

def main():
    items = []
    for i in range(1, 11):
        items.append(
            double_value.create_bulk_run_item(input=DoubleInput(n=i))
        )
    
    results = double_value.run_many(items)
    
    output = []
    for i in range(1, 11):
        # results[i-1] is EmptyModel(result=i*2)
        res_val = getattr(results[i-1], 'result', None)
        if res_val is None and isinstance(results[i-1], dict):
            res_val = results[i-1].get('result')
            
        output.append({
            "n": i,
            "result": res_val
        })
        
    output.sort(key=lambda x: x["n"])
    
    with open("/tmp/results.json", "w") as f:
        json.dump(output, f, indent=2)
        
    print("Wrote results to /tmp/results.json")

if __name__ == "__main__":
    main()
