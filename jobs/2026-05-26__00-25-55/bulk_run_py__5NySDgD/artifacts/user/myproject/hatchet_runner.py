import json
from shared import hatchet, double_value, DoubleInput

def main():
    inputs_data = [DoubleInput(n=i) for i in range(1, 11)]
    items = [double_value.create_bulk_run_item(input=data) for data in inputs_data]
    
    print(f"Triggering bulk run for {len(items)} items...")
    results = double_value.run_many(items)
    
    final_results = []
    for data, res in zip(inputs_data, results):
        # res should be a DoubleOutput instance
        final_results.append({"n": data.n, "result": res.result})

    # Ensure sorted by n ascending
    final_results.sort(key=lambda x: x["n"])
    
    print(f"Writing results to /tmp/results.json")
    with open("/tmp/results.json", "w") as f:
        json.dump(final_results, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()
