import os
import subprocess
import time
import signal
import pytest

PROJECT_DIR = "/home/user/project"
OUTPUT_FILE = os.path.join(PROJECT_DIR, "output.txt")

@pytest.fixture(scope="module", autouse=True)
def start_worker():
    # Clean up output file from any previous run
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        
    worker_script = os.path.join(PROJECT_DIR, "worker.py")
    assert os.path.exists(worker_script), f"worker.py not found at {worker_script}"

    # Start the worker
    process = subprocess.Popen(
        ["python3", "worker.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for the worker to initialize
    time.sleep(5)
    
    yield
    
    # Shut down the worker
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=10)

def test_trigger_script_executes_successfully():
    """Priority 1: Run the trigger.py script and verify it completes without errors."""
    trigger_script = os.path.join(PROJECT_DIR, "trigger.py")
    assert os.path.exists(trigger_script), f"trigger.py not found at {trigger_script}"

    result = subprocess.run(
        ["python3", "trigger.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, \
        f"'python3 trigger.py' failed with exit code {result.returncode}.\nStdout: {result.stdout}\nStderr: {result.stderr}"

def test_output_file_contains_expected_result():
    """Priority 3: Verify the output.txt file contains exactly 'Hello World!'."""
    assert os.path.exists(OUTPUT_FILE), f"Output file {OUTPUT_FILE} does not exist. The trigger script might not have created it."
    
    with open(OUTPUT_FILE, "r") as f:
        content = f.read().strip()
        
    assert content == "Hello World!", \
        f"Expected output.txt to contain exactly 'Hello World!', but got: '{content}'"

def test_amika_validation():
    """Use the amika CLI to do the validation as requested."""
    # Assuming amika CLI is available and has a validate/verify command
    try:
        result = subprocess.run(
            ["amika", "validate", "--target", PROJECT_DIR],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        # If amika is installed and runs, check its return code
        assert result.returncode == 0, f"Amika validation failed: {result.stderr}"
    except FileNotFoundError:
        # If amika CLI is not found, we skip or fail depending on strictness.
        # Since the prompt requires using it, we should fail if it's missing.
        pytest.fail("amika CLI not found in PATH. It is required for validation.")
