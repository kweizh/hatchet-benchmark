import os
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/app"

def test_hatchet_event_push():
    reason = "The task requires a Hatchet workflow that processes orders and waits for an approval event. The script should push three order:created events and three order:approved events. The final outputs should be written as a JSON array to output.json."
    truth = "Verify that the file /home/user/app/output.json exists. Verify the JSON content is an array of length 3. Verify the JSON array contains objects with order_id '101', '102', and '103'."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_hatchet_event_push"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
