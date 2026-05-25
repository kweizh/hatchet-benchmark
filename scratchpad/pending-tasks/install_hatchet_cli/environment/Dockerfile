FROM ubuntu:22.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip bash ripgrep tar && \
    pip3 install --upgrade pip && \
    pip3 install pytest pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/hatchet-install && chmod 0755 /home/user/hatchet-install

LABEL Author="generate-harbor-tasks"
LABEL Description="Minimal Ubuntu 22.04 environment for installing the Hatchet CLI from the official install script during the task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip bash ripgrep tar
#   - always required pip3 packages: pytest, pytest-json-ctrf (pytest is installed via pip instead of apt
#     because the apt-shipped python3-pytest on Ubuntu 22.04 is too old for pytest-json-ctrf)
#   - /home/user/hatchet-install: empty project directory where the agent will install and exercise the Hatchet CLI
#   - Hatchet CLI is intentionally NOT pre-installed; the agent must install it during the task via:
#       curl -fsSL https://install.hatchet.run/install.sh | bash
