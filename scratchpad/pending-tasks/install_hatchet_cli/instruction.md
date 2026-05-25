# Install the Hatchet CLI

## Background
Hatchet is a distributed task queue and workflow engine that ships an official command-line tool, `hatchet`. The CLI is used to manage profiles, run quickstart projects, start workers, and trigger workflows. Before any of that is possible, the `hatchet` binary needs to be available on the system. In this task you must install the Hatchet CLI inside a fresh container and confirm that it is reachable on the shell `PATH`.

## Requirements
- Install the Hatchet CLI using the official install script published by the Hatchet team.
- After installation, the `hatchet` binary must be discoverable through `PATH` so that running `hatchet` from any working directory succeeds.
- Record the output of the version command to a log file so the verifier can inspect what was installed.

## Implementation Hints
- The recommended install method on Linux/macOS/WSL is the official shell installer fetched with `curl` from `https://install.hatchet.run/install.sh` and piped to `bash`.
- The install script downloads the appropriate binary for the platform and places it in a directory that is already on the system `PATH` (for example `/usr/local/bin`).
- Use `hatchet --version` to confirm the installation succeeded; the command prints the installed semantic version (for example `0.86.29`) on stdout.
- Make sure standard prerequisites such as `curl`, `tar`, and `ca-certificates` are available before running the installer (they are pre-installed in the provided environment).

## Acceptance Criteria
- Project path: /home/user/hatchet-install
- Log file: /home/user/hatchet-install/install.log
- `which hatchet` resolves to an executable file that exists on the system `PATH`.
- Running `hatchet --version` exits with status `0` and prints a semantic version string of the form `MAJOR.MINOR.PATCH` (optionally prefixed with `v`) on stdout.
- The log file `/home/user/hatchet-install/install.log` exists, is non-empty, and contains the semantic version reported by `hatchet --version`.

