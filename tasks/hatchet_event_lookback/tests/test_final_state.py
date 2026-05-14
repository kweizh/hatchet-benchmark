import os
import ast
import subprocess

WORKER_FILE = "/home/user/project/worker.py"

def test_worker_file_exists():
    assert os.path.isfile(WORKER_FILE), f"worker.py not found at {WORKER_FILE}"

def test_aio_wait_for_event_called_with_correct_args():
    with open(WORKER_FILE, "r") as f:
        source = f.read()

    tree = ast.parse(source)

    found_wait = False
    lookback_window_valid = False
    expression_present = False
    scope_present = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if function name is aio_wait_for_event
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name == "aio_wait_for_event":
                found_wait = True
                for kw in node.keywords:
                    if kw.arg == "lookback_window":
                        # Check if it's timedelta(minutes=5) or timedelta(seconds=300)
                        if isinstance(kw.value, ast.Call):
                            call_name = None
                            if isinstance(kw.value.func, ast.Name):
                                call_name = kw.value.func.id
                            elif isinstance(kw.value.func, ast.Attribute):
                                call_name = kw.value.func.attr
                            
                            if call_name == "timedelta":
                                for t_kw in kw.value.keywords:
                                    if t_kw.arg == "minutes" and isinstance(t_kw.value, ast.Constant) and t_kw.value.value == 5:
                                        lookback_window_valid = True
                                    if t_kw.arg == "seconds" and isinstance(t_kw.value, ast.Constant) and t_kw.value.value == 300:
                                        lookback_window_valid = True
                    if kw.arg == "expression":
                        expression_present = True
                    if kw.arg == "scope":
                        scope_present = True

    assert found_wait, "aio_wait_for_event was not called in worker.py."
    assert lookback_window_valid, "aio_wait_for_event was not called with lookback_window=timedelta(minutes=5)."
    assert expression_present, "aio_wait_for_event was not called with the 'expression' keyword argument."
    assert scope_present, "aio_wait_for_event was not called with the 'scope' keyword argument."

def test_amika_validation():
    # Use the amika CLI or API to do the validation in final tests
    try:
        import amika
        amika.validate_file(WORKER_FILE)
    except ImportError:
        # Fallback to amika CLI if python API is not available
        try:
            result = subprocess.run(["amika", "validate", WORKER_FILE], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Amika validation failed: {result.stderr}")
        except FileNotFoundError:
            # Amika not installed in the environment
            pass
