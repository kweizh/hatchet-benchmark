import os
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/project"

def test_cross_language_execution():
    reason = "The task requires creating a cross-language workflow where a Python worker triggers a TypeScript worker using a stub."
    truth = "Run the script `bash run.sh` in `/home/user/project`. Verify that it executes successfully. Read `/home/user/project/output.log` and verify it contains exactly 'Hello from Python received by TS'."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_cross_language_execution"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
