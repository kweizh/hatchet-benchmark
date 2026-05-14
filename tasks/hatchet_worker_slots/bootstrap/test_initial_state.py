import os
import subprocess

def test_initial_state():
    # Verify we are in the correct directory (or it exists)
    assert os.path.exists("/home/user"), "User directory should exist"
    
    # Verify node is installed
    result = subprocess.run(["node", "-v"], capture_output=True, text=True)
    assert result.returncode == 0, "Node.js must be installed"
    
    # Verify npm is installed
    result = subprocess.run(["npm", "-v"], capture_output=True, text=True)
    assert result.returncode == 0, "npm must be installed"
