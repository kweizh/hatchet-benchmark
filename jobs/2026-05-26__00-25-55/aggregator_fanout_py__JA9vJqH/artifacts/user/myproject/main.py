import json
import asyncio
import threading
from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()

class PrepareOutput(BaseModel):
    urls: list[str]

class ScrapeOneInput(BaseModel):
    url: str

class ScrapeOneOutput(BaseModel):
    url: str
    length: int

class ScrapeAllOutput(BaseModel):
    pages: list[ScrapeOneOutput]

# Define the child workflow 'scrape_one'
scrape_one_wf = hatchet.workflow(name="scrape_one")

@scrape_one_wf.task(name="scrape_one")
def scrape_one(input: ScrapeOneInput, ctx) -> ScrapeOneOutput:
    url = input.url
    return {
        "url": url,
        "length": len(url) * 7
    }

# Define the main DAG workflow 'doc_pipeline'
doc_pipeline_wf = hatchet.workflow(name="doc_pipeline")

@doc_pipeline_wf.task(name="prepare")
def prepare(input, ctx) -> PrepareOutput:
    return {
        "urls": ["https://example.com/a", "/b", "/c"]
    }

@doc_pipeline_wf.task(name="scrape_all", parents=[prepare])
async def scrape_all(input, ctx) -> ScrapeAllOutput:
    # Get urls from prepare task
    prepare_output: PrepareOutput = ctx.task_output(prepare)
    urls = prepare_output.urls
    
    # Create bulk run items for scrape_one workflow
    bulk_items = [
        scrape_one_wf.create_bulk_run_item(input={"url": url})
        for url in urls
    ]
    
    # Run many child workflows
    results = await scrape_one_wf.aio_run_many(bulk_items)
    
    # Extract results from child runs
    pages = []
    for result in results:
        pages.append(result)
        
    return {"pages": pages}

@doc_pipeline_wf.task(name="aggregate", parents=[scrape_all])
def aggregate(input, ctx):
    # Read pages from scrape_all task
    scrape_all_output: ScrapeAllOutput = ctx.task_output(scrape_all)
    pages = scrape_all_output.pages
    
    total_length = sum(p.length for p in pages)
    count = len(pages)
    
    result = {
        "total_length": total_length,
        "count": count
    }
    
    # Write to /tmp/result.json
    with open("/tmp/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f)
        
    return result

async def main():
    # Start worker in a separate thread
    worker = hatchet.worker("doc-worker")
    worker.register_workflow(scrape_one_wf)
    worker.register_workflow(doc_pipeline_wf)
    
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    # Wait a bit for worker to register
    await asyncio.sleep(5)
    
    print("Triggering doc_pipeline...")
    # Trigger the pipeline
    run = await doc_pipeline_wf.aio_run({})
    
    print("Waiting for run to complete...")
    # Wait for the run to complete
    result = await run.result()
    print(f"Run completed. Result: {result}")
    
    # The aggregate task writes the file, so we are done.
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
