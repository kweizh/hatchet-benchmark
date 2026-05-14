FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest python3-venv bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Python 3 environment for Hatchet agent loop task."

RUN mkdir -p /home/user/agent_loop

# Container contents:
#   - Python 3 and venv installed.
#   - /home/user/agent_loop directory created for the project.

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]