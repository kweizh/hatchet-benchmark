FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    pip3 install --break-system-packages pytest-json-ctrf hatchet-sdk pydantic && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/myproject

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet Python SDK task environment for the bulk_run_py task targeting Hatchet Cloud."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - hatchet-sdk and pydantic installed via pip3 for the Hatchet Python task
#   - /home/user/myproject: empty project directory where the executor implements the worker and runner
