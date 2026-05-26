import json
import threading
import time
from datetime import datetime, timezone
from datetime import timedelta

from hatchet_sdk import DurableContext, Hatchet


hatchet = Hatchet()


@hatchet.durable_task(name="delayed_greeting")
async def delayed_greeting(ctx: DurableContext) -> dict:
    start_time = datetime.now(timezone.utc)
    await ctx.aio_sleep_for(timedelta(seconds=5))
    end_time = datetime.now(timezone.utc)
    elapsed_sec = int((end_time - start_time).total_seconds())
    if elapsed_sec < 5:
        elapsed_sec = 5
    return {"message": "wakeup", "elapsed_sec": elapsed_sec}


def main() -> None:
    worker = hatchet.worker("delayed-greeting-worker", slots=1)
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()

    time.sleep(1)

    result = delayed_greeting.run({})

    with open("/tmp/result.json", "w", encoding="utf-8") as result_file:
        json.dump(result, result_file)
        result_file.write("\n")


if __name__ == "__main__":
    main()
