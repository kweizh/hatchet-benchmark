import os
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/app"

def test_hatchet_typescript_worker():
    reason = "The task requires a Hatchet TypeScript worker that registers a workflow and processes an event."
    truth = "Run `npm install`, then run `npm run worker &` in the background, wait 5 seconds. Then run `npm run trigger`. Wait 5 seconds. Verify that `/home/user/app/output.log` exists and contains exactly `{\"message\":\"Welcome Alice\"}`."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_hatchet_typescript_worker"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
