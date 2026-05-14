FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk

RUN curl -fsSL https://install.hatchet.run/install.sh | bash

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Hatchet task environment with Python SDK and CLI installed."

RUN mkdir -p /home/user/hatchet_project

# Container contents:
#   - python3, pip, pytest
#   - hatchet-sdk installed via pip
#   - hatchet CLI installed via install.sh
#   - /home/user/hatchet_project - base directory for the project

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
