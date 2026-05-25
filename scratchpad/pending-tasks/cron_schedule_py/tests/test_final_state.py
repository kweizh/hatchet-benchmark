import os
import pathlib
from datetime import datetime

HEARTBEAT_PATH = "/tmp/heartbeats.log"
PROJECT_DIR = "/home/user/myproject"


def _read_non_empty_lines(path):
    with open(path, "r") as f:
        raw = f.read()
    return [line.strip() for line in raw.splitlines() if line.strip()]


def test_heartbeats_file_exists():
    """The cron-triggered heartbeat task must produce /tmp/heartbeats.log."""
    assert os.path.isfile(HEARTBEAT_PATH), (
        f"Expected heartbeat log {HEARTBEAT_PATH} to exist after the runner finishes. "
        "The cron-triggered task must append at least one ISO timestamp line to this file."
    )


def test_heartbeats_file_has_at_least_one_line():
    lines = _read_non_empty_lines(HEARTBEAT_PATH)
    assert len(lines) >= 1, (
        f"Expected at least one non-empty line in {HEARTBEAT_PATH}, found {len(lines)}. "
        "This indicates the cron trigger never fired or the worker did not pick up the run."
    )


def test_at_least_one_line_is_valid_iso_timestamp():
    lines = _read_non_empty_lines(HEARTBEAT_PATH)
    parsed_any = False
    parse_errors = []
    for line in lines:
        try:
            datetime.fromisoformat(line)
            parsed_any = True
            break
        except ValueError as exc:
            parse_errors.append(f"{line!r}: {exc}")
    assert parsed_any, (
        f"Expected at least one ISO 8601 timestamp line in {HEARTBEAT_PATH} "
        f"parseable by datetime.fromisoformat. "
        f"Lines found: {lines!r}. Parse errors: {parse_errors!r}."
    )


def test_runner_source_present_in_project_dir():
    """A Python source file must exist in the project directory, indicating the agent wrote real code."""
    project_path = pathlib.Path(PROJECT_DIR)
    assert project_path.is_dir(), (
        f"Expected project directory {PROJECT_DIR} to exist."
    )
    py_files = list(project_path.rglob("*.py"))
    assert py_files, (
        f"Expected at least one .py source file under {PROJECT_DIR} (the Hatchet "
        "heartbeat task and runner). Found none."
    )
