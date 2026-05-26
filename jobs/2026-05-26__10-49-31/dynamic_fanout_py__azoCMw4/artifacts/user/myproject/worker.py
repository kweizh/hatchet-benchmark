"""
Start a Hatchet worker that registers BOTH process_batch and square_item.
Authentication is via the HATCHET_CLIENT_TOKEN environment variable.
"""

from workflows import hatchet, process_batch, square_item

worker = hatchet.worker(
    name="fanout-worker",
    workflows=[process_batch, square_item],
)

if __name__ == "__main__":
    worker.start()
