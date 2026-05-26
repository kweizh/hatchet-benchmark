FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    pip3 install --break-system-packages pytest-json-ctrf hatchet-sdk pydantic && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/myproject && chmod 0755 /home/user/myproject

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet Python SDK task environment for per-key concurrency control. Connects to Hatchet Cloud via HATCHET_CLIENT_TOKEN."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - target SDK pip3 package: hatchet-sdk (Hatchet Python SDK; connects to Hatchet Cloud)
#   - supporting pip3 package: pydantic (used as input_validator for Hatchet tasks)
#   - /home/user/myproject: empty project directory where the executor implements
#     the worker + runner code that produces /tmp/runs.log
