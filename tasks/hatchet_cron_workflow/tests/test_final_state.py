import os
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/app"

def test_cron_workflow_execution():
    reason = "The task requires a Hatchet workflow scheduled with cron `* * * * *` that reads a JSON file and writes the processed count to output.log."
    truth = "Run `python worker.py &` in the background from `/home/user/app`. Wait for 65 seconds to allow the cron trigger to execute. Then verify that the file `/home/user/app/output.log` exists and contains the exact text `Processed 3 records`."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_cron_workflow_execution"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
