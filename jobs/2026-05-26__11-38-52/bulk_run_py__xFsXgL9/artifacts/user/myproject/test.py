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
    
    try:
        results = double_value.run_many(items)
        print("Results:", results)
        
        final_results = []
        for r in results:
            res = r.result()
            print("Result result:", res)
            final_results.append(res)
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
