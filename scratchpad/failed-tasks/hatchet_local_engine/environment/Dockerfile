FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash \
        docker.io docker-compose-v2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk

RUN curl -fsSL https://install.hatchet.run/install.sh | bash

RUN mkdir -p /home/user/hatchet-project && chmod 0755 /home/user/hatchet-project

LABEL Author="any-task-builder"
LABEL Description="Hatchet local engine event routing task environment with Docker and Hatchet SDK."

# Container contents:
#   - curl ca-certificates git python3 python3-pip python3-pytest bash docker.io docker-compose-v2
#   - hatchet-sdk installed via pip
#   - hatchet CLI installed via install script
#   - /home/user/hatchet-project as the base directory for the project

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
