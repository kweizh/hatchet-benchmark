FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Hatchet durable execution and failure recovery test environment."

RUN mkdir -p /home/user/project

# Container contents:
#   - hatchet-sdk installed for Python 3.
#   - /home/user/project  — Empty project directory

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
