from workflows import hatchet, process_batch, square_item

def main():
    worker = hatchet.worker("test-worker")
    worker.register_workflow(square_item)
    worker.register_workflow(process_batch)
    worker.start()

if __name__ == "__main__":
    main()
