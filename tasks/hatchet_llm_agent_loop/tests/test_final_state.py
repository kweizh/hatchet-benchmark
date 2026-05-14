import os
import pytest
from amika import Amika

PROJECT_DIR = "/home/user/agent_loop"

def test_hatchet_agent_loop():
    reason = "The task requires creating an LLM-powered agent loop using Hatchet durable tasks that streams progress and stops when a goal is reached."
    truth = "Run the trigger script `python run.py` in `/home/user/agent_loop`. Verify that the script succeeds and `/home/user/agent_loop/output.log` is created. Read `output.log` and verify it contains streamed thoughts from multiple iterations of the mock LLM call, and that the loop terminated when `goal_reached` was true."
    
    verifier = Amika()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        trajectory_dir="/logs/verifier/amika/test_hatchet_agent_loop"
    )
    assert result.status == "pass", f"Amika verification failed: {result.reason}"
