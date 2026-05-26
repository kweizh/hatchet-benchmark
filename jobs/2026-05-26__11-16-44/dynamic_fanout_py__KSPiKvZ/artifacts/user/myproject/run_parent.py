import json

from workflows import ProcessBatchInput, process_batch_workflow


def main() -> None:
    result = process_batch_workflow.run(ProcessBatchInput(items=[1, 2, 3, 4, 5]))
    payload = result["process_batch"]
    with open("/tmp/result.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


if __name__ == "__main__":
    main()
