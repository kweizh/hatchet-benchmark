import os
import re
import glob

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = "/home/user/myproject/output.log"


def _read_log() -> str:
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    assert content.strip(), f"Log file {LOG_FILE} is empty."
    return content


def test_output_log_exists_and_nonempty():
    _ = _read_log()


def test_run1_celsius_to_fahrenheit_result_in_log():
    """Run 1: value=100 unit=C -> celsius=100 fahrenheit=212"""
    content = _read_log()
    pattern = re.compile(
        r"^RUN1_RESULT:\s+celsius=100(?:\.0+)?\s+fahrenheit=212(?:\.0+)?\s*$",
        re.MULTILINE,
    )
    assert pattern.search(content) is not None, (
        "Expected log line matching 'RUN1_RESULT: celsius=100(.0) fahrenheit=212(.0)' "
        f"in {LOG_FILE}, but it was not found. Log content:\n{content}"
    )


def test_run2_fahrenheit_to_celsius_result_in_log():
    """Run 2: value=32 unit=F -> celsius=0 fahrenheit=32"""
    content = _read_log()
    pattern = re.compile(
        r"^RUN2_RESULT:\s+celsius=0(?:\.0+)?\s+fahrenheit=32(?:\.0+)?\s*$",
        re.MULTILINE,
    )
    assert pattern.search(content) is not None, (
        "Expected log line matching 'RUN2_RESULT: celsius=0(.0) fahrenheit=32(.0)' "
        f"in {LOG_FILE}, but it was not found. Log content:\n{content}"
    )


def test_run3_validation_error_in_log():
    """Run 3: value='abc' unit='K' -> VALIDATION_ERROR (must fail Pydantic validation)"""
    content = _read_log()
    err_pattern = re.compile(r"^RUN3_RESULT:\s+VALIDATION_ERROR\s*$", re.MULTILINE)
    assert err_pattern.search(content) is not None, (
        "Expected log line matching 'RUN3_RESULT: VALIDATION_ERROR' "
        f"in {LOG_FILE}, but it was not found. Log content:\n{content}"
    )
    # Must NOT contain a successful numeric celsius/fahrenheit result for run 3.
    bad_success = re.compile(
        r"^RUN3_RESULT:\s+celsius=", re.MULTILINE
    )
    assert bad_success.search(content) is None, (
        "Run 3 must fail Pydantic validation; found a successful celsius result for RUN3 in log."
    )


def _find_python_sources():
    py_files = []
    for path in glob.glob(os.path.join(PROJECT_DIR, "**/*.py"), recursive=True):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                py_files.append((path, f.read()))
        except OSError:
            continue
    return py_files


def test_worker_registers_task_with_run_id_suffix():
    """The Hatchet task name must resolve to temp-converter-${ZEALT_RUN_ID}."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID env var must be set in verifier environment."
    sources = _find_python_sources()
    assert sources, f"No python source files found under {PROJECT_DIR}."

    literal = f"temp-converter-{run_id}"
    found_literal = any(literal in code for _, code in sources)

    # Or the source uses an f-string / concatenation referencing ZEALT_RUN_ID with the temp-converter prefix.
    expr_pattern = re.compile(
        r"temp-converter-[^\"']*(\{[^}]*ZEALT_RUN_ID[^}]*\}|\"\s*\+\s*[^\"']*ZEALT_RUN_ID|\$\{ZEALT_RUN_ID\})",
    )
    found_expr = any(expr_pattern.search(code) is not None for _, code in sources)
    # Also accept simpler patterns where ZEALT_RUN_ID is read into a variable then concatenated
    simple_pattern = re.compile(
        r"temp-converter-",
    )
    env_ref_pattern = re.compile(r"ZEALT_RUN_ID")
    has_prefix = any(simple_pattern.search(code) for _, code in sources)
    has_env_ref = any(env_ref_pattern.search(code) for _, code in sources)

    assert found_literal or found_expr or (has_prefix and has_env_ref), (
        "Worker source must register a Hatchet task whose name is "
        f"'temp-converter-{run_id}' (using the ZEALT_RUN_ID env var as suffix)."
    )


def test_task_uses_pydantic_input_validator():
    """Task decorator must declare input_validator referencing a Pydantic model with the right fields."""
    sources = _find_python_sources()
    assert sources, f"No python source files found under {PROJECT_DIR}."

    # Must use input_validator=
    validator_re = re.compile(r"input_validator\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
    validator_names = []
    for _, code in sources:
        validator_names.extend(validator_re.findall(code))
    assert validator_names, (
        "Expected the task decorator to declare input_validator=<PydanticModel>; "
        "no such usage found in project sources."
    )

    # Find at least one Pydantic BaseModel class with `value: float` and `unit: Literal["C", "F"]`.
    has_value_field_re = re.compile(r"\bvalue\s*:\s*float\b")
    has_unit_field_re = re.compile(
        r"\bunit\s*:\s*Literal\[\s*[\"']C[\"']\s*,\s*[\"']F[\"']\s*\]"
    )
    has_base_model = False
    has_value = False
    has_unit = False
    for _, code in sources:
        if "BaseModel" in code:
            has_base_model = True
        if has_value_field_re.search(code):
            has_value = True
        if has_unit_field_re.search(code):
            has_unit = True

    assert has_base_model, "Expected at least one Pydantic BaseModel class in project sources."
    assert has_value, "Expected a Pydantic model field declaration `value: float`."
    assert has_unit, (
        "Expected a Pydantic model field declaration `unit: Literal[\"C\", \"F\"]`."
    )
