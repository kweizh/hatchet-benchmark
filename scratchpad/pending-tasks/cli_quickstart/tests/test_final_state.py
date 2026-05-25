import os
import re
import shutil
import subprocess
from pathlib import Path


PROJECT_DIR = "/home/user/quickstart-project"


def test_hatchet_cli_still_available_on_path():
    assert shutil.which("hatchet") is not None, (
        "The hatchet CLI binary is no longer available on PATH after task execution."
    )


def test_hatchet_cli_reports_version():
    result = subprocess.run(
        ["hatchet", "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"`hatchet --version` exited with code {result.returncode}; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    version_text = (result.stdout or "") + (result.stderr or "")
    assert re.search(r"\d+\.\d+\.\d+", version_text), (
        f"`hatchet --version` did not print a recognizable version string. "
        f"Output was: {version_text!r}"
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected the Hatchet quickstart project directory at {PROJECT_DIR}, "
        "but it does not exist or is not a directory."
    )


def test_project_contains_python_source_file():
    py_files = list(Path(PROJECT_DIR).rglob("*.py"))
    listing = [
        str(p.relative_to(PROJECT_DIR))
        for p in Path(PROJECT_DIR).rglob("*")
        if p.is_file()
    ]
    assert len(py_files) >= 1, (
        f"Expected at least one Python source file (*.py) under {PROJECT_DIR}, "
        f"but none were found. Files present: {listing}"
    )


def test_project_contains_readme():
    candidates = [
        os.path.join(PROJECT_DIR, "README.md"),
        os.path.join(PROJECT_DIR, "README"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]
    top_level = os.listdir(PROJECT_DIR) if os.path.isdir(PROJECT_DIR) else "<dir missing>"
    assert existing, (
        f"Expected a top-level README (README.md or README) inside {PROJECT_DIR}, "
        f"but none was found. Top-level entries: {top_level}"
    )
    readme_path = existing[0]
    assert os.path.getsize(readme_path) > 0, (
        f"The README at {readme_path} exists but is empty."
    )


def test_project_contains_hatchet_yaml():
    hatchet_yaml = os.path.join(PROJECT_DIR, "hatchet.yaml")
    top_level = os.listdir(PROJECT_DIR) if os.path.isdir(PROJECT_DIR) else "<dir missing>"
    assert os.path.isfile(hatchet_yaml), (
        f"Expected `hatchet.yaml` (part of the standard Hatchet quickstart scaffold) "
        f"at {hatchet_yaml}, but it does not exist. Top-level entries: {top_level}"
    )
