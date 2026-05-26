from tasks import double_value, hatchet


def main() -> None:
    worker = hatchet.worker("double-value-worker", workflows=[double_value])
    worker.start()


if __name__ == "__main__":
    main()
