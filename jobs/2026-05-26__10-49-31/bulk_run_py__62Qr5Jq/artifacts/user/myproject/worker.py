from hatchet_sdk import Hatchet
from task import hatchet, double_value


def main():
    worker = hatchet.worker("double-value-worker", slots=10)
    worker.register_workflow(double_value)
    worker.start()


if __name__ == "__main__":
    main()
