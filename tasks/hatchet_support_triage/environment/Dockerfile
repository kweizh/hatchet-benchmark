FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk pydantic

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Hatchet Support Agent Workflow task environment with Hatchet Python SDK."

RUN mkdir -p /home/user/support-agent

# Container contents:
#   - python3, pip, pytest installed
#   - hatchet-sdk, pydantic installed
#   - /home/user/support-agent directory created

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
