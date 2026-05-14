FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk pydantic

RUN mkdir -p /home/user/hatchet-worker && chmod 0755 /home/user/hatchet-worker

LABEL Author="any-task-builder"
LABEL Description="Hatchet Python Worker task environment with hatchet-sdk pre-installed."

# Container contents:
#   - python3, python3-pip, python3-pytest
#   - hatchet-sdk installed globally
#   - /home/user/hatchet-worker directory for the project

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
