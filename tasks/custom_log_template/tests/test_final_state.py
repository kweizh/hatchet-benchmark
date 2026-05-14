import os
import re
import subprocess

PROJECT_DIR = "/home/user/myrepo"
LOG_FILE = os.path.join(PROJECT_DIR, "log_output.txt")

TEMPLATE = 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
REVSET = "all() ~ root() ~ @"

EXPECTED_DESCRIPTIONS = ("Initial commit", "Add feature B", "Fix bug C")


def _run_jj_log_template(template: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "jj",
            "log",
            "--no-graph",
            "-r",
            REVSET,
            "-T",
            template,
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_log_output_file_exists():
    assert os.path.isfile(LOG_FILE), (
        f"Expected {LOG_FILE} to exist after running the task."
    )


def test_log_output_file_not_empty():
    assert os.path.getsize(LOG_FILE) > 0, (
        f"Expected {LOG_FILE} to be non-empty after running the task."
    )


def test_log_output_matches_jj_log_template():
    """Priority 1: re-run the same jj log command and diff its output against the file."""
    result = _run_jj_log_template(TEMPLATE)
    assert result.returncode == 0, (
        f"`jj log` with the expected template failed in {PROJECT_DIR}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        file_contents = f.read()
    assert file_contents == result.stdout, (
        "Contents of log_output.txt do not match the output of\n"
        f"  jj log --no-graph -r '{REVSET}' -T '{TEMPLATE}'\n"
        f"--- log_output.txt ---\n{file_contents!r}\n"
        f"--- jj log stdout ---\n{result.stdout!r}"
    )


def test_log_output_contains_all_expected_descriptions():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for desc in EXPECTED_DESCRIPTIONS:
        assert content.count(desc) == 1, (
            f"Expected description {desc!r} to appear exactly once in {LOG_FILE}, "
            f"but it appeared {content.count(desc)} times.\nContents:\n{content}"
        )


def test_log_output_line_format():
    """Every non-empty line must look like '<short_commit_id> <first_line_of_description>'."""
    line_re = re.compile(r"^[0-9a-f]+ .+$")
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]
    assert lines, f"Expected at least one non-empty line in {LOG_FILE}."
    for line in lines:
        assert line_re.match(line), (
            f"Line does not match '<short_commit_id> <first_line_of_description>' "
            f"format: {line!r}"
        )


def test_log_output_has_three_lines():
    """The file must have exactly 3 non-empty lines (one per real commit)."""
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        non_empty_lines = [l for l in f.read().splitlines() if l.strip()]
    assert len(non_empty_lines) == 3, (
        f"Expected exactly 3 non-empty lines in {LOG_FILE}, got {len(non_empty_lines)}.\n"
        f"Lines: {non_empty_lines!r}"
    )
