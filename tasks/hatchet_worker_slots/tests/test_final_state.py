import os
import subprocess
import time
import json

def test_final_state():
    project_dir = "/home/user/hatchet-slots"
    assert os.path.exists(project_dir), "Project directory must exist"
    
    # Verify package.json exists
    assert os.path.exists(os.path.join(project_dir, "package.json")), "package.json must exist"
    
    # Verify typescript-sdk is installed
    with open(os.path.join(project_dir, "package.json")) as f:
        pkg = json.load(f)
        deps = pkg.get("dependencies", {})
        assert "@hatchet-dev/typescript-sdk" in deps, "Hatchet SDK must be installed"
        
    # We won't strictly run the code because it requires a real Hatchet server connection
    # and we don't want to enforce a specific file name or structure beyond what the agent creates.
    # However, we check if the agent created the necessary scripts.
    ts_files = [f for f in os.listdir(project_dir) if f.endswith(".ts")]
    assert len(ts_files) >= 1, "There should be at least one TypeScript file created"
    
    # Check if sleepFor is used in the codebase
    found_sleep_for = False
    for ts_file in ts_files:
        with open(os.path.join(project_dir, ts_file)) as f:
            content = f.read()
            if "sleepFor" in content:
                found_sleep_for = True
                break
                
    assert found_sleep_for, "The code must use ctx.sleepFor to demonstrate durable sleep"
