"""
worker.py – Registers the static rate limit on Hatchet Cloud and then
starts the Hatchet worker.  This module is executed inside a child
process spawned by the orchestrator so that `worker.start()` (which
blocks) does not prevent the parent from dispatching runs.
"""

from hatchet_sdk import RateLimitDuration

from task import RATE_LIMIT_KEY, call_external_api, hatchet


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Register / update the static rate limit on Hatchet Cloud.
    #    limit=5, duration=MINUTE → at most 5 calls per 60-second window.
    # ------------------------------------------------------------------
    hatchet.rate_limits.put(RATE_LIMIT_KEY, 5, RateLimitDuration.MINUTE)
    print(f"[worker] rate limit registered: key={RATE_LIMIT_KEY} limit=5/min")

    # ------------------------------------------------------------------
    # 2. Build and start the worker.
    #    slots=20 ensures local capacity is never the bottleneck.
    # ------------------------------------------------------------------
    worker = hatchet.worker(
        "rate-limit-worker",
        slots=20,
        workflows=[call_external_api],
    )
    print("[worker] starting – waiting for tasks …")
    worker.start()  # blocks until the process is terminated


if __name__ == "__main__":
    main()
