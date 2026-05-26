"""
Document-Processing Fan-out + Aggregate DAG using Hatchet Python SDK.

Topology:
  doc_pipeline DAG:  prepare -> scrape_all -> aggregate
  scrape_one: standalone child workflow (one per URL)
"""

import asyncio
import json

from pydantic import BaseModel

from hatchet_sdk import Hatchet

# ---------------------------------------------------------------------------
# Hatchet client (reads HATCHET_CLIENT_TOKEN automatically)
# ---------------------------------------------------------------------------
hatchet = Hatchet()

# ---------------------------------------------------------------------------
# Input / output models
# ---------------------------------------------------------------------------

class ScrapeOneInput(BaseModel):
    url: str


# ---------------------------------------------------------------------------
# Child workflow: scrape_one
# Registered as its own standalone workflow so it can be spawned at runtime.
# ---------------------------------------------------------------------------
scrape_one = hatchet.workflow(name="scrape_one", input_validator=ScrapeOneInput)


@scrape_one.task()
def scrape_one_task(input: ScrapeOneInput, ctx) -> dict:
    """Simulate scraping a single URL: length = len(url) * 7."""
    return {"url": input.url, "length": len(input.url) * 7}


# ---------------------------------------------------------------------------
# Parent DAG workflow: doc_pipeline
# ---------------------------------------------------------------------------
doc_pipeline = hatchet.workflow(name="doc_pipeline")


@doc_pipeline.task()
def prepare(input, ctx) -> dict:
    """Return the list of URLs to process."""
    return {"urls": ["https://example.com/a", "/b", "/c"]}


@doc_pipeline.task(parents=[prepare])
async def scrape_all(input, ctx) -> dict:
    """Fan-out: spawn one scrape_one child workflow per URL."""
    urls = ctx.task_output(prepare)["urls"]

    bulk_items = [
        scrape_one.create_bulk_run_item(input=ScrapeOneInput(url=url))
        for url in urls
    ]

    results = await scrape_one.aio_run_many(bulk_items)
    pages = [{"url": r["url"], "length": r["length"]} for r in results]
    return {"pages": pages}


@doc_pipeline.task(parents=[scrape_all])
def aggregate(input, ctx) -> dict:
    """Aggregate all scraped page results into a summary."""
    pages = ctx.task_output(scrape_all)["pages"]
    total_length = sum(p["length"] for p in pages)
    count = len(pages)
    return {"total_length": total_length, "count": count}


# ---------------------------------------------------------------------------
# Worker + trigger
# ---------------------------------------------------------------------------

async def main():
    # Create the worker in the main thread / event loop.
    worker = hatchet.worker(
        "doc-pipeline-worker",
        workflows=[doc_pipeline, scrape_one],
    )

    # Start the worker as an async background task so the event loop keeps running.
    worker_task = asyncio.create_task(worker._aio_start())

    # Give the worker a moment to connect and register workflows.
    print("Starting worker, waiting for registration…")
    await asyncio.sleep(5)

    # Trigger the doc_pipeline DAG exactly once and wait for completion.
    print("Triggering doc_pipeline…")
    result = await doc_pipeline.aio_run()
    print(f"doc_pipeline completed. Raw result: {result}")

    # The leaf task (aggregate) returns {"total_length": ..., "count": ...}.
    if isinstance(result, dict):
        aggregate_output = result
    else:
        aggregate_output = dict(result)

    print(f"Aggregate output: {aggregate_output}")

    # Persist to /tmp/result.json
    with open("/tmp/result.json", "w", encoding="utf-8") as f:
        json.dump(aggregate_output, f)

    print("Written to /tmp/result.json")
    print(json.dumps(aggregate_output, indent=2))

    # Cancel the worker task now that we have our result.
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
