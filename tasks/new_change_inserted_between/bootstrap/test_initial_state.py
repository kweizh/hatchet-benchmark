import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myrepo"


def _jj(args, cwd=PROJECT_DIR):
    return subprocess.run(
        ["jj"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_jj_binary_available():
    assert shutil.which("jj") is not None, "jj binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_project_is_colocated_jj_repo():
    assert os.path.isdir(os.path.join(PROJECT_DIR, ".jj")), \
        f".jj directory missing in {PROJECT_DIR}; expected a jj repository."
    assert os.path.isdir(os.path.join(PROJECT_DIR, ".git")), \
        f".git directory missing in {PROJECT_DIR}; expected a colocated jj/Git repo."


def test_jj_user_identity_configured():
    name = _jj(["config", "get", "user.name"])
    email = _jj(["config", "get", "user.email"])
    assert name.returncode == 0 and name.stdout.strip(), \
        f"user.name is not configured for jj: {name.stderr}"
    assert email.returncode == 0 and email.stdout.strip(), \
        f"user.email is not configured for jj: {email.stderr}"


def test_setup_commit_exists_with_setup_py():
    result = _jj([
        "log", "-r", 'description(substring:"Setup")',
        "--no-graph", "-T", 'change_id ++ "\\n"',
    ])
    assert result.returncode == 0, f"jj log failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert len(lines) == 1, \
        f"Expected exactly one 'Setup' change, got {len(lines)}: {result.stdout!r}"

    files = _jj([
        "file", "list", "-r", 'description(substring:"Setup")',
    ])
    assert files.returncode == 0, f"jj file list (Setup) failed: {files.stderr}"
    file_list = [l.strip() for l in files.stdout.splitlines() if l.strip()]
    assert "setup.py" in file_list, \
        f"Expected setup.py to exist in the Setup change, got: {file_list}"


def test_implementation_commit_exists_with_main_py():
    result = _jj([
        "log", "-r", 'description(substring:"Implementation")',
        "--no-graph", "-T", 'change_id ++ "\\n"',
    ])
    assert result.returncode == 0, f"jj log failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert len(lines) == 1, \
        f"Expected exactly one 'Implementation' change, got {len(lines)}: {result.stdout!r}"

    files = _jj([
        "file", "list", "-r", 'description(substring:"Implementation")',
    ])
    assert files.returncode == 0, f"jj file list (Implementation) failed: {files.stderr}"
    file_list = [l.strip() for l in files.stdout.splitlines() if l.strip()]
    assert "main.py" in file_list, \
        f"Expected main.py to exist in the Implementation change, got: {file_list}"


def test_tests_commit_exists_with_test_main_py():
    result = _jj([
        "log", "-r", 'description(substring:"Tests")',
        "--no-graph", "-T", 'change_id ++ "\\n"',
    ])
    assert result.returncode == 0, f"jj log failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert len(lines) == 1, \
        f"Expected exactly one 'Tests' change, got {len(lines)}: {result.stdout!r}"

    files = _jj([
        "file", "list", "-r", 'description(substring:"Tests")',
    ])
    assert files.returncode == 0, f"jj file list (Tests) failed: {files.stderr}"
    file_list = [l.strip() for l in files.stdout.splitlines() if l.strip()]
    assert "test_main.py" in file_list, \
        f"Expected test_main.py to exist in the Tests change, got: {file_list}"


def test_initial_stack_is_linear_setup_impl_tests():
    # Parent of Implementation must be Setup.
    parent_impl = _jj([
        "log", "-r", 'description(substring:"Implementation")-',
        "--no-graph", "-T", 'description.first_line() ++ "\\n"',
    ])
    assert parent_impl.returncode == 0, f"jj log failed: {parent_impl.stderr}"
    lines = [l for l in parent_impl.stdout.splitlines() if l.strip()]
    assert lines and lines[0] == "Setup", \
        f"Expected parent of Implementation to be Setup, got: {parent_impl.stdout!r}"

    # Parent of Tests must be Implementation.
    parent_tests = _jj([
        "log", "-r", 'description(substring:"Tests")-',
        "--no-graph", "-T", 'description.first_line() ++ "\\n"',
    ])
    assert parent_tests.returncode == 0, f"jj log failed: {parent_tests.stderr}"
    lines = [l for l in parent_tests.stdout.splitlines() if l.strip()]
    assert lines and lines[0] == "Implementation", \
        f"Expected parent of Tests to be Implementation, got: {parent_tests.stdout!r}"


def test_working_copy_is_empty_child_of_tests():
    # Parent of working copy must be Tests.
    parent_wc = _jj([
        "log", "-r", "@-",
        "--no-graph", "-T", 'description.first_line() ++ "\\n"',
    ])
    assert parent_wc.returncode == 0, f"jj log failed: {parent_wc.stderr}"
    lines = [l for l in parent_wc.stdout.splitlines() if l.strip()]
    assert lines and lines[0] == "Tests", \
        f"Expected parent of working copy to be Tests, got: {parent_wc.stdout!r}"

    # Working copy must be empty (no diff vs parent).
    diff = _jj(["diff", "-r", "@", "--summary"])
    assert diff.returncode == 0, f"jj diff failed: {diff.stderr}"
    assert diff.stdout.strip() == "", \
        f"Expected the working-copy change to be empty, got diff: {diff.stdout!r}"
