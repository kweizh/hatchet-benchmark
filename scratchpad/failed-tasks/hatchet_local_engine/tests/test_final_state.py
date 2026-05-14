import os
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/hatchet-project"

def test_hatchet_event_routing():
    reason = "The task requires a Hatchet workflow that writes 'Event routed successfully' to output.log when triggered by 'user:created' event."
    truth = "Verify that the file /home/user/hatchet-project/output.log exists and contains the exact text 'Event routed successfully'."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_hatchet_event_routing"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
