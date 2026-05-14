import os
import subprocess
import json
import pytest

PROJECT_DIR = "/home/user/myproject"
SCRIPT_FILE = os.path.join(PROJECT_DIR, "main.py")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "output.json")

def test_script_exists():
    assert os.path.isfile(SCRIPT_FILE), f"Script file {SCRIPT_FILE} does not exist."

def test_script_execution():
    result = subprocess.run(
        ["python3", "main.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Script execution failed with exit code {result.returncode}.\nStdout: {result.stdout}\nStderr: {result.stderr}"

def test_output_json_contents():
    assert os.path.isfile(OUTPUT_FILE), f"Output file {OUTPUT_FILE} was not created."
    
    with open(OUTPUT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse {OUTPUT_FILE} as JSON: {e}")
            
    assert isinstance(data, list), "Output JSON should be a list of dictionaries."
    
    expected_items = [{"processed": "APPLE"}, {"processed": "BANANA"}, {"processed": "CHERRY"}]
    
    for item in expected_items:
        assert item in data, f"Expected item {item} not found in output data: {data}"
    
    assert len(data) == 3, f"Expected exactly 3 items in the output, got {len(data)}: {data}"