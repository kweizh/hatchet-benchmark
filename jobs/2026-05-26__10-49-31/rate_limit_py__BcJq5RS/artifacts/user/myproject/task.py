"""
call_external_api – Hatchet task definition with static rate limiting.

The rate-limit key and the task object are created at import time so that
both the worker process and the orchestrator process share the same
definition module.
"""

import os
from datetime import datetime, timezone

from hatchet_sdk import Context, Hatchet, RateLimit, RateLimitDuration

# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------

RUN_ID = os.environ["ZEALT_RUN_ID"]
RATE_LIMIT_KEY = f"ext-api-{RUN_ID}"
LOG_FILE = "/tmp/rate_log.txt"

# ---------------------------------------------------------------------------
# Hatchet client
# ---------------------------------------------------------------------------

hatchet = Hatchet(debug=True)

# ---------------------------------------------------------------------------
# Task definition
# ---------------------------------------------------------------------------


@hatchet.task(
    name="call_external_api",
    rate_limits=[RateLimit(static_key=RATE_LIMIT_KEY, units=1)],
)
def call_external_api(context: Context) -> dict:
    """Append a UTC ISO-8601 timestamp to the rate log file."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    with open(LOG_FILE, "a") as fh:
        fh.write(ts + "\n")
    return {"timestamp": ts}
