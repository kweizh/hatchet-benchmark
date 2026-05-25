import os
import shutil


PROJECT_DIR = "/home/user/hatchet-install"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hatchet_cli_not_yet_installed():
    assert shutil.which("hatchet") is None, (
        "Expected the `hatchet` CLI to NOT be installed before the task starts, "
        "but it was found on PATH."
    )


def test_curl_available():
    assert shutil.which("curl") is not None, (
        "`curl` must be available in PATH so the official Hatchet install script can be fetched."
    )


def test_bash_available():
    assert shutil.which("bash") is not None, (
        "`bash` must be available in PATH so the official Hatchet install script can be executed."
    )


def test_ca_certificates_present():
    # The official install script downloads release artifacts over HTTPS;
    # the system CA bundle must be present for TLS verification to succeed.
    candidates = [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    ]
    assert any(os.path.isfile(p) for p in candidates), (
        "Expected a system CA certificate bundle to be installed so HTTPS downloads succeed."
    )
