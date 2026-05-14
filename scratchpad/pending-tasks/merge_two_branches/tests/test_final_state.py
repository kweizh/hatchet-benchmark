import subprocess

PROJECT_DIR = "/home/user/myrepo"

MERGE_REV = 'description(substring:"Merge branches")'


def _jj(args, check=True):
    result = subprocess.run(
        ["jj", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    if check:
        assert result.returncode == 0, (
            f"`jj {' '.join(args)}` failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
    return result


def _log_lines(revset: str, template: str):
    result = _jj(["log", "-r", revset, "--no-graph", "-T", template])
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_exactly_one_merge_commit_exists():
    lines = _log_lines(MERGE_REV, 'change_id ++ "\\n"')
    assert len(lines) == 1, (
        f"Expected exactly one commit with description 'Merge branches', got {len(lines)}: {lines}"
    )


def test_merge_commit_description_is_exact():
    result = _jj(["log", "-r", MERGE_REV, "--no-graph", "-T", "description.first_line()"])
    assert result.stdout.strip() == "Merge branches", (
        f"Expected merge commit description to be exactly 'Merge branches', got {result.stdout!r}"
    )


def test_merge_commit_has_exactly_two_parents_with_expected_descriptions():
    parent_descs = _log_lines(f"{MERGE_REV}-", 'description.first_line() ++ "\\n"')
    assert len(parent_descs) == 2, (
        f"Expected the merge commit to have exactly 2 parents, got {len(parent_descs)}: {parent_descs}"
    )
    assert set(parent_descs) == {"Branch X commit", "Branch Y commit"}, (
        f"Expected merge commit parents to be 'Branch X commit' and 'Branch Y commit', got {parent_descs}"
    )


def test_merge_commit_parent_change_ids_match_branch_tips():
    parent_ids = set(_log_lines(f"{MERGE_REV}-", 'change_id ++ "\\n"'))
    branch_x_id = set(_log_lines("branch_x", 'change_id ++ "\\n"'))
    branch_y_id = set(_log_lines("branch_y", 'change_id ++ "\\n"'))
    assert len(parent_ids) == 2, (
        f"Expected exactly 2 distinct parent change IDs for the merge commit, got: {parent_ids}"
    )
    assert len(branch_x_id) == 1, f"Expected one change ID for branch_x, got: {branch_x_id}"
    assert len(branch_y_id) == 1, f"Expected one change ID for branch_y, got: {branch_y_id}"
    expected = branch_x_id | branch_y_id
    assert parent_ids == expected, (
        f"Expected the merge commit's parents to be exactly the tips of branch_x and branch_y, got parents={parent_ids} expected={expected}"
    )


def test_branch_x_bookmark_not_moved():
    result = _jj(["log", "-r", "branch_x", "--no-graph", "-T", "description.first_line()"])
    assert result.stdout.strip() == "Branch X commit", (
        f"Expected branch_x to still point to 'Branch X commit' (unmoved), got {result.stdout!r}"
    )


def test_branch_y_bookmark_not_moved():
    result = _jj(["log", "-r", "branch_y", "--no-graph", "-T", "description.first_line()"])
    assert result.stdout.strip() == "Branch Y commit", (
        f"Expected branch_y to still point to 'Branch Y commit' (unmoved), got {result.stdout!r}"
    )


def test_merge_commit_contains_shared_file():
    result = _jj(["file", "show", "-r", MERGE_REV, "shared.txt"])
    assert result.stdout.strip() == "shared content", (
        f"Expected shared.txt at merge commit to contain 'shared content', got {result.stdout!r}"
    )


def test_merge_commit_contains_x_file():
    result = _jj(["file", "show", "-r", MERGE_REV, "x.txt"])
    assert result.stdout.strip() == "x", (
        f"Expected x.txt at merge commit to contain 'x', got {result.stdout!r}"
    )


def test_merge_commit_contains_y_file():
    result = _jj(["file", "show", "-r", MERGE_REV, "y.txt"])
    assert result.stdout.strip() == "y", (
        f"Expected y.txt at merge commit to contain 'y', got {result.stdout!r}"
    )
