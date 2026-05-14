from workflow import workflow, hatchet

def main():
    # Create a worker
    worker = hatchet.worker("order-worker")
    
    # Register the OrderWorkflow
    worker.register_workflow(workflow)
    
    # Start the worker
    worker.start()

if __name__ == "__main__":
    main()
