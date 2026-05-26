from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

@hatchet.task(name="square_item")
def square_item(workflow_input, context: Context) -> dict:
    input_data = context.workflow_input
    item = input_data.get("item")
    return {"square": item * item}

@hatchet.task(name="process_batch")
async def process_batch(workflow_input, context: Context) -> dict:
    input_data = context.workflow_input
    items = input_data.get("items", [])
    
    # Spawn children using the square_item Standalone workflow
    child_runs = [
        square_item.create_bulk_run_item(input={"item": item})
        for item in items
    ]
    
    # aio_run_many returns the results in order
    results = await square_item.aio_run_many(child_runs)
    
    # results is a list of return values from the square_item task
    squares = [r["square"] for r in results]
    
    return {"squares": squares}
