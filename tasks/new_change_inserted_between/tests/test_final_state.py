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


def test_exactly_one_add_dependencies_change_exists():
    result = _jj([
        "log", "-r", 'description(substring:"Add dependencies")',
        "--no-graph", "-T", 'change_id ++ "\\n"',
    ])
    assert result.returncode == 0, \
        f"jj log for 'Add dependencies' failed: {result.stderr}"
    ids = [l for l in result.stdout.splitlines() if l.strip()]
    assert len(ids) == 1, \
        f"Expected exactly one change with description 'Add dependencies', got {len(ids)}: {result.stdout!r}"


def test_parent_of_add_dependencies_is_setup():
    result = _jj([
        "log", "-r", 'description(substring:"Add dependencies")-',
        "--no-graph", "-T", 'description.first_line() ++ "\\n"',
    ])
    assert result.returncode == 0, \
        f"jj log for parent of 'Add dependencies' failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert lines and lines[0] == "Setup", \
        f"Expected parent of 'Add dependencies' to be 'Setup', got: {result.stdout!r}"


def test_child_of_add_dependencies_is_implementation():
    result = _jj([
        "log", "-r", 'description(substring:"Add dependencies")+',
        "--no-graph", "-T", 'description.first_line() ++ "\\n"',
    ])
    assert result.returncode == 0, \
        f"jj log for child of 'Add dependencies' failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert lines and lines[0] == "Implementation", \
        f"Expected child of 'Add dependencies' to be 'Implementation', got: {result.stdout!r}"


def test_add_dependencies_contains_requirements_txt():
    result = _jj([
        "file", "show", "-r", 'description(substring:"Add dependencies")',
        "requirements.txt",
    ])
    assert result.returncode == 0, \
        f"jj file show requirements.txt failed: {result.stderr}"
    content = result.stdout.strip()
    assert content == "pytest==8.0.0", \
        f"Expected requirements.txt to contain 'pytest==8.0.0', got: {result.stdout!r}"


def test_requirements_txt_is_only_new_file_in_add_dependencies():
    # The Add dependencies change should add exactly one file (requirements.txt)
    # relative to its parent Setup.
    result = _jj([
        "diff", "-r", 'description(substring:"Add dependencies")', "--summary",
    ])
    assert result.returncode == 0, f"jj diff --summary failed: {result.stderr}"
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    assert lines == ["A requirements.txt"], \
        f"Expected only 'A requirements.txt' in diff, got: {result.stdout!r}"


def test_working_copy_contains_all_four_files():
    result = _jj(["file", "list", "-r", "@"])
    assert result.returncode == 0, f"jj file list -r @ failed: {result.stderr}"
    files = sorted(l.strip() for l in result.stdout.splitlines() if l.strip())
    expected = sorted(["setup.py", "requirements.txt", "main.py", "test_main.py"])
    assert files == expected, \
        f"Expected working-copy tip files {expected}, got: {files}"


def test_original_descriptions_still_exist():
    for desc in ("Setup", "Implementation", "Tests"):
        result = _jj([
            "log", "-r", f'description(substring:"{desc}")',
            "--no-graph", "-T", 'description.first_line() ++ "\\n"',
        ])
        assert result.returncode == 0, \
            f"jj log for description '{desc}' failed: {result.stderr}"
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        # "Add dependencies" must not match these substrings.
        assert desc in lines, \
            f"Expected a change with description '{desc}' to still exist, got: {result.stdout!r}"


def test_parent_of_tests_is_implementation_after_rebase():
    # After the insertion, the downstream stack must remain
    # Setup -> Add dependencies -> Implementation -> Tests.
    result = _jj([
        "log", "-r", 'description(substring:"Tests")-',
        "--no-graph", "-T", 'description.first_line() ++ "\\n"',
    ])
    assert result.returncode == 0, f"jj log failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert lines and lines[0] == "Implementation", \
        f"Expected parent of 'Tests' to be 'Implementation' after rebase, got: {result.stdout!r}"
