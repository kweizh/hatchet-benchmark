"""Run the Hatchet worker (meant to be launched as a subprocess)."""
from diamond_workflow import hatchet, workflow

if __name__ == "__main__":
    worker = hatchet.worker("diamond-worker", workflows=[workflow])
    worker.start()
