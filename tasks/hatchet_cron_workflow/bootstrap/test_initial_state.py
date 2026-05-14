import os
import shutil
import json

def test_python_available():
    assert shutil.which("python") is not None, "python binary not found in PATH."

def test_app_directory_exists():
    assert os.path.isdir("/home/user/app"), "/home/user/app directory does not exist."

def test_records_file_exists():
    records_path = "/home/user/app/records.json"
    assert os.path.isfile(records_path), f"Records file {records_path} does not exist."
    with open(records_path) as f:
        data = json.load(f)
    assert len(data) == 3, "Expected 3 records in records.json"
    assert data[0]["id"] == 1, "Expected first record to have id 1"
