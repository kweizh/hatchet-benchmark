import subprocess

PROJECT_DIR = "/home/user/myrepo"


def test_user_name_set_via_get():
    result = subprocess.run(
        ["jj", "config", "get", "user.name"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected 'jj config get user.name' to succeed, got "
        f"returncode={result.returncode}, stderr={result.stderr}"
    )
    assert result.stdout.strip() == "Alice Example", (
        f"Expected user.name to be 'Alice Example', got: {result.stdout!r}"
    )


def test_user_email_set_via_get():
    result = subprocess.run(
        ["jj", "config", "get", "user.email"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected 'jj config get user.email' to succeed, got "
        f"returncode={result.returncode}, stderr={result.stderr}"
    )
    assert result.stdout.strip() == "alice@example.com", (
        f"Expected user.email to be 'alice@example.com', got: {result.stdout!r}"
    )


def test_user_name_appears_in_config_list():
    result = subprocess.run(
        ["jj", "config", "list", "user"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected 'jj config list user' to succeed, got "
        f"returncode={result.returncode}, stderr={result.stderr}"
    )
    assert "user.name" in result.stdout and "Alice Example" in result.stdout, (
        f"Expected 'jj config list user' output to contain user.name=\"Alice Example\", "
        f"got: {result.stdout!r}"
    )


def test_user_email_appears_in_config_list():
    result = subprocess.run(
        ["jj", "config", "list", "user"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected 'jj config list user' to succeed, got "
        f"returncode={result.returncode}, stderr={result.stderr}"
    )
    assert "user.email" in result.stdout and "alice@example.com" in result.stdout, (
        f"Expected 'jj config list user' output to contain user.email=\"alice@example.com\", "
        f"got: {result.stdout!r}"
    )


def test_user_config_scope_is_user():
    """Ensure the values come from the user scope, not the repo scope."""
    result = subprocess.run(
        ["jj", "config", "list", "--user", "user"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected 'jj config list --user user' to succeed, got "
        f"returncode={result.returncode}, stderr={result.stderr}"
    )
    assert "Alice Example" in result.stdout, (
        f"Expected the user-scope config to contain 'Alice Example', got: {result.stdout!r}"
    )
    assert "alice@example.com" in result.stdout, (
        f"Expected the user-scope config to contain 'alice@example.com', got: {result.stdout!r}"
    )
