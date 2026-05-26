from tasks import WORKER_NAME, hatchet, process_payment


def main() -> None:
    worker = hatchet.worker(WORKER_NAME, slots=4, workflows=[process_payment])
    worker.start()


if __name__ == "__main__":
    main()
