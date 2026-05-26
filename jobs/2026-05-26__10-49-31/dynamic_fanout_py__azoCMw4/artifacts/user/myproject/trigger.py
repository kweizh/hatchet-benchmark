"""
Trigger the process_batch workflow once with {"items": [1, 2, 3, 4, 5]},
wait for it to complete, then write the result to /tmp/result.json.
"""

import json

from workflows import ProcessBatchInput, hatchet, process_batch


def main() -> None:
    raw = process_batch.run(
        input=ProcessBatchInput(items=[1, 2, 3, 4, 5]),
        wait_for_result=True,
    )

    print("Raw workflow result:", raw)

    # The SDK wraps the task output under the task-name key; unwrap it.
    # raw == {"process_batch": {"squares": [...]}}
    if "process_batch" in raw:
        result = raw["process_batch"]
    else:
        result = raw

    print("Final result:", result)

    with open("/tmp/result.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh)

    print("Result written to /tmp/result.json")


if __name__ == "__main__":
    main()
