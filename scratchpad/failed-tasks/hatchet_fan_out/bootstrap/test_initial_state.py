import os
import pytest

PROJECT_DIR = "/home/user/hatchet_project"

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_input_csv_exists():
    csv_path = os.path.join(PROJECT_DIR, "input.csv")
    assert os.path.isfile(csv_path), f"Input file {csv_path} does not exist."

def test_input_csv_content():
    csv_path = os.path.join(PROJECT_DIR, "input.csv")
    with open(csv_path) as f:
        content = f.read()
    assert "id,name" in content, "Expected 'id,name' header in input.csv."
    lines = content.strip().split('\n')
    assert len(lines) == 4, f"Expected 3 data rows plus 1 header in input.csv, got {len(lines)} lines."
