FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm i -g tsx && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/myproject && \
    cd /home/user/myproject && \
    npm init -y >/dev/null && \
    npm install @hatchet-dev/typescript-sdk typescript >/dev/null

LABEL Author="generate-harbor-tasks"
LABEL Description="Node.js v24 environment with @hatchet-dev/typescript-sdk and tsx preinstalled for a Hatchet TypeScript cron schedule task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (via NodeSource)
#   - tsx installed globally for running TypeScript directly
#   - /home/user/myproject: pre-initialized Node project with @hatchet-dev/typescript-sdk and typescript installed
