FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash \
        docker.io docker-compose-v2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk

RUN curl -fsSL https://install.hatchet.run/install.sh | bash

RUN mkdir -p /home/user/app && chmod 0755 /home/user/app

LABEL Author="any-task-builder"
LABEL Description="Hatchet task environment with Hatchet CLI, SDK, and Docker installed."

# Container contents:
#   - always required libs: curl ca-certificates git python3 python3-pip python3-pytest bash
#   - docker.io for running Hatchet local server
#   - hatchet-sdk installed via pip
#   - hatchet CLI installed via curl
#   - /home/user/app: base directory for the project

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
