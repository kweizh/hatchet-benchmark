import os
import subprocess
import time
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/project"

def test_run_and_verify_failure_recovery():
    # Ensure HATCHET_CLIENT_TOKEN is set
    assert "HATCHET_CLIENT_TOKEN" in os.environ, "HATCHET_CLIENT_TOKEN environment variable is missing."
    
    reason = "The task requires a Hatchet durable task that crashes midway on the first run, then successfully resumes from checkpoint upon worker restart without repeating the first step."
    truth = """
## Verification Steps
1. Navigate to `/home/user/project`.
2. Start the worker script in the background: `bash run.sh &`
3. Give the worker a few seconds to connect to Hatchet Cloud.
4. Run the trigger script: `python3 trigger.py`
5. Verify that `trigger.py` completes successfully (exit code 0).
6. Verify that `/home/user/project/crashed.flag` exists, proving the crash occurred.
7. Verify that `/home/user/project/output.log` exists.
8. Read `/home/user/project/output.log` and verify it contains exactly one line with `step1` and exactly one line with `step2` (in that order).
"""
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_hatchet_failure_recovery"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
