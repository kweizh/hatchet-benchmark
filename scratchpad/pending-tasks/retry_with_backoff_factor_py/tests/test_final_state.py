import os
import re
import time
from datetime import datetime

import pytest

LOG_FILE = "/home/user/myproject/output.log"

ATTEMPT_LINE_RE = re.compile(
    r"^Attempt retry_count=(\d+) timestamp=(\S+)\s*$",
    re.MULTILINE,
)


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set for verification."
    return run_id


def _workflow_name() -> str:
    return f"backoff-task-{_run_id()}"


def _read_log() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task completes."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _parsed_attempts():
    content = _read_log()
    matches = ATTEMPT_LINE_RE.findall(content)
    return content, matches


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task completes."
    )


def test_log_file_contains_four_attempt_lines_in_order():
    content, matches = _parsed_attempts()
    assert len(matches) == 4, (
        f"Expected exactly 4 attempt lines in {LOG_FILE} matching "
        f"'Attempt retry_count=<N> timestamp=<ISO8601>', but found {len(matches)}. "
        f"Log contents:\n{content}"
    )
    retry_counts = [int(m[0]) for m in matches]
    assert retry_counts == [0, 1, 2, 3], (
        f"Expected retry_count values to be [0, 1, 2, 3] in order, got {retry_counts}. "
        f"Log contents:\n{content}"
    )


def test_attempt_timestamps_show_exponential_backoff():
    content, matches = _parsed_attempts()
    assert len(matches) == 4, (
        f"Expected exactly 4 attempt lines to compute backoff gaps; "
        f"found {len(matches)}.\nLog contents:\n{content}"
    )

    timestamps = []
    for idx, (_, ts) in enumerate(matches):
        try:
            # datetime.fromisoformat handles e.g. "2024-01-01T12:00:00+00:00"
            # but not the trailing "Z"; normalize for safety.
            ts_norm = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
            dt = datetime.fromisoformat(ts_norm)
        except ValueError as e:
            raise AssertionError(
                f"Attempt {idx} timestamp {ts!r} is not a valid ISO-8601 datetime: {e}.\n"
                f"Log contents:\n{content}"
            )
        timestamps.append(dt)

    seconds = [t.timestamp() for t in timestamps]
    gap1 = seconds[1] - seconds[0]
    gap2 = seconds[2] - seconds[1]
    gap3 = seconds[3] - seconds[2]

    assert gap1 > 0 and gap2 > 0 and gap3 > 0, (
        f"Expected strictly positive inter-attempt gaps, got "
        f"gap1={gap1:.3f}s, gap2={gap2:.3f}s, gap3={gap3:.3f}s."
    )

    assert gap1 >= 1.0, (
        f"Expected gap1 to be at least 1.0s for backoff_factor=2 "
        f"(observed ~2s plus scheduling overhead), got gap1={gap1:.3f}s."
    )

    ratio_2_1 = gap2 / gap1
    ratio_3_2 = gap3 / gap2

    assert 1.5 <= ratio_2_1 <= 3.5, (
        f"Expected gap2 to be roughly 2x gap1 (ratio between 1.5 and 3.5), "
        f"got gap1={gap1:.3f}s, gap2={gap2:.3f}s, ratio={ratio_2_1:.3f}."
    )
    assert 1.5 <= ratio_3_2 <= 3.5, (
        f"Expected gap3 to be roughly 2x gap2 (ratio between 1.5 and 3.5), "
        f"got gap2={gap2:.3f}s, gap3={gap3:.3f}s, ratio={ratio_3_2:.3f}."
    )


def test_log_file_contains_success_line():
    content = _read_log()
    expected = "Task succeeded after 4 attempts"
    assert expected in content, (
        f"Expected log file {LOG_FILE} to contain the final outcome line "
        f"'{expected}', but it was not found. Log contents:\n{content}"
    )


def test_hatchet_workflow_succeeded_with_four_attempts():
    """Query the real Hatchet server via the Python SDK and verify the workflow
    run for `backoff-task-${ZEALT_RUN_ID}` succeeded with exactly 4 attempts
    (i.e. 3 retries occurred before success).
    """
    token = os.environ.get("HATCHET_CLIENT_TOKEN")
    server_url = os.environ.get("HATCHET_SERVER_URL")
    assert token, "HATCHET_CLIENT_TOKEN must be set to query the Hatchet server."
    assert server_url, "HATCHET_SERVER_URL must be set to query the Hatchet server."

    from hatchet_sdk import Hatchet

    hatchet = Hatchet()

    workflow_name = _workflow_name()

    # 1. Locate the workflow by name.
    workflows = hatchet.workflows.list()
    rows = getattr(workflows, "rows", None) or []
    matching = [w for w in rows if getattr(w, "name", None) == workflow_name]
    assert matching, (
        f"No Hatchet workflow named '{workflow_name}' was found on the server. "
        f"Workflows available: {[getattr(w, 'name', None) for w in rows]}"
    )
    workflow = matching[0]
    workflow_id = getattr(workflow, "metadata", None)
    workflow_id = (
        getattr(workflow_id, "id", None)
        if workflow_id is not None
        else getattr(workflow, "id", None)
    )
    assert workflow_id, f"Could not resolve workflow id for '{workflow_name}'."

    # 2. Find the most recent run for that workflow, retrying briefly to allow
    #    the server to finalize the run state.
    runs = None
    deadline = time.time() + 60
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            runs = hatchet.runs.list(workflow_ids=[workflow_id])
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2)
    assert runs is not None, (
        f"Failed to list runs for workflow '{workflow_name}': {last_err}"
    )

    run_rows = getattr(runs, "rows", None) or []
    assert run_rows, f"Hatchet workflow '{workflow_name}' has no recorded runs."
    latest = run_rows[0]

    status = getattr(latest, "status", None)
    status_str = getattr(status, "value", status)
    assert str(status_str).upper() in {"SUCCEEDED", "COMPLETED", "SUCCESS"}, (
        f"Expected latest run of '{workflow_name}' to have succeeded, "
        f"got status={status_str}."
    )

    # 3. Confirm the run had exactly 4 attempts (initial attempt + 3 retries).
    tasks = getattr(latest, "tasks", None) or []
    attempts: int | None = None
    if tasks:
        first = tasks[0]
        rc = getattr(first, "retry_count", None)
        if rc is not None:
            attempts = rc + 1
        else:
            attempts = (
                getattr(first, "attempt", None)
                or getattr(first, "attempt_number", None)
            )

    if attempts is None:
        # Fallback: fetch run detail and inspect its task runs / event history.
        run_id = getattr(latest, "metadata", None)
        run_id = (
            getattr(run_id, "id", None)
            if run_id is not None
            else getattr(latest, "id", None)
        )
        assert run_id, "Could not resolve the latest run id from the Hatchet SDK response."
        detail = hatchet.runs.get(run_id)
        detail_tasks = (
            getattr(detail, "tasks", None)
            or getattr(detail, "task_runs", None)
            or []
        )
        assert detail_tasks, (
            f"Run {run_id} has no task runs to inspect for attempt count."
        )
        first = detail_tasks[0]
        rc = getattr(first, "retry_count", None)
        if rc is not None:
            attempts = rc + 1
        else:
            attempts = getattr(first, "attempt", None)
        assert attempts is not None, (
            f"Could not determine attempt count for run {run_id}."
        )

    assert attempts == 4, (
        f"Expected workflow '{workflow_name}' to have completed in exactly 4 "
        f"attempts (3 retries + 1 success), but observed {attempts} attempt(s)."
    )
