import asyncio
import json
import threading
from typing import Any, Dict

from hatchet_sdk import Hatchet
from pydantic import BaseModel

hatchet = Hatchet()


class ScrapeOneInput(BaseModel):
    url: str


# Child workflow: scrape_one
scrape_one = hatchet.workflow(name="scrape_one", input_validator=ScrapeOneInput)


@scrape_one.task(name="scrape_one")
def scrape_one_task(input: ScrapeOneInput, ctx) -> Dict[str, Any]:
    url = input.url
    return {"url": url, "length": len(url) * 7}


# DAG workflow: doc_pipeline
doc_pipeline = hatchet.workflow(name="doc_pipeline")


@doc_pipeline.task(name="prepare")
def prepare(input: Dict[str, Any], ctx) -> Dict[str, Any]:
    return {"urls": ["https://example.com/a", "/b", "/c"]}


@doc_pipeline.task(name="scrape_all", parents=[prepare])
async def scrape_all(input: Dict[str, Any], ctx) -> Dict[str, Any]:
    urls = ctx.task_output(prepare)["urls"]
    bulk_items = [
        scrape_one.create_bulk_run_item(input={"url": url}) for url in urls
    ]
    pages = await scrape_one.aio_run_many(bulk_items)
    return {"pages": pages}


@doc_pipeline.task(name="aggregate", parents=[scrape_all])
def aggregate(input: Dict[str, Any], ctx) -> Dict[str, Any]:
    pages = ctx.task_output(scrape_all)["pages"]
    total_length = sum(page["length"] for page in pages)
    return {"total_length": total_length, "count": len(pages)}


async def main() -> None:
    worker = hatchet.worker(
        name="doc-pipeline-worker",
        workflows=[doc_pipeline, scrape_one],
    )
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()

    result = await doc_pipeline.aio_run({})

    if isinstance(result, dict) and "aggregate" in result:
        aggregate_output = result["aggregate"]
    else:
        aggregate_output = result

    with open("/tmp/result.json", "w", encoding="utf-8") as handle:
        json.dump(aggregate_output, handle)


if __name__ == "__main__":
    asyncio.run(main())
