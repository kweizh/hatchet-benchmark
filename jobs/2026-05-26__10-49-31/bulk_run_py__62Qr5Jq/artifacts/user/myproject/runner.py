import json
from task import double_value, DoubleInput


def main():
    # Build bulk run items for n = 1..10
    items = [
        double_value.create_bulk_run_item(input=DoubleInput(n=n))
        for n in range(1, 11)
    ]

    # Submit all 10 in a single bulk call and wait for all results
    results = double_value.run_many(items)

    # results are returned in the same order as the input list
    # pair each result with its corresponding n value
    output = sorted(
        [{"n": n, "result": results[i].result} for i, n in enumerate(range(1, 11))],
        key=lambda x: x["n"],
    )

    with open("/tmp/results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Written /tmp/results.json:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
