from workflows import hatchet, process_batch_workflow, square_item_workflow


def main() -> None:
    worker = hatchet.worker(
        "dynamic-fanout-worker",
        workflows=[square_item_workflow, process_batch_workflow],
    )
    worker.start()


if __name__ == "__main__":
    main()
