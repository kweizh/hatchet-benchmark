FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep tar && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Pre-install the Hatchet CLI from the official install script.
# The script auto-detects an install directory; we force it to /usr/local/bin
# so that the `hatchet` binary is globally available on PATH for both the
# task executor and the verifier.
RUN INSTALL_DIR=/usr/local/bin curl -fsSL https://install.hatchet.run/install.sh | INSTALL_DIR=/usr/local/bin bash && \
    hatchet --version

RUN mkdir -p /home/user && chmod 0755 /home/user

# Pre-configure a Hatchet CLI profile so that `hatchet quickstart` does not
# refuse to run with the "No Hatchet profiles configured" error. The
# quickstart subcommand only requires that at least one profile exists in
# ~/.hatchet/profiles.yaml; it does NOT need to talk to a live server to
# scaffold the project files locally.
RUN mkdir -p /root/.hatchet && \
    touch /root/.hatchet/config.yaml && \
    printf '%s\n' \
        'profiles:' \
        '  local:' \
        '    tenantId: 00000000-0000-0000-0000-000000000000' \
        '    name: local' \
        '    token: placeholder-token-for-quickstart-scaffolding' \
        '    expiresAt: 2099-12-31T23:59:59Z' \
        '    apiServerURL: http://localhost:8888' \
        '    grpcHostPort: localhost:7077' \
        '    tlsStrategy: none' \
        > /root/.hatchet/profiles.yaml && \
    chmod 0600 /root/.hatchet/profiles.yaml

LABEL Author="generate-harbor-tasks"
LABEL Description="Ubuntu 24.04 environment with the Hatchet CLI pre-installed and a pre-configured local profile so that `hatchet quickstart` can scaffold a project under /home/user."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep tar
#   - always required pip3 packages: pytest-json-ctrf
#   - Hatchet CLI installed via the official install script into /usr/local/bin/hatchet
#   - Pre-configured Hatchet profile at /root/.hatchet/profiles.yaml so that
#     `hatchet quickstart` can run non-interactively for the task
#   - /home/user as the executor's working directory
