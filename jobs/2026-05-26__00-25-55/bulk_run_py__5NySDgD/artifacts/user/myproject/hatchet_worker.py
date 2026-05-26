from shared import hatchet, double_value

def main():
    worker = hatchet.worker("bulk-worker")
    worker.register_workflow(double_value)
    worker.start()

if __name__ == "__main__":
    main()
