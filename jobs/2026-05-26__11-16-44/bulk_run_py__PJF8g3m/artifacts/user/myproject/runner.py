import json
from typing import Any

from tasks import DoubleValueInput, double_value


def _extract_result(item: Any) -> int:
    if hasattr(item, "model_dump"):
        return item.model_dump()["result"]
    if isinstance(item, dict):
        return item["result"]
    return getattr(item, "result")


def main() -> None:
    bulk_items = [
        double_value.create_bulk_run_item(input=DoubleValueInput(n=n))
        for n in range(1, 11)
    ]
    results = double_value.run_many(bulk_items)

    output = [
        {"n": n, "result": _extract_result(result)}
        for n, result in zip(range(1, 11), results)
    ]

    with open("/tmp/results.json", "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
