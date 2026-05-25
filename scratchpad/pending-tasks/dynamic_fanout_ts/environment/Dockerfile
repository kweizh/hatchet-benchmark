FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/myproject && \
    cd /home/user/myproject && \
    cat >package.json <<'EOF'
{
  "name": "dynamic-fanout-ts",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "tsx index.ts"
  },
  "dependencies": {
    "@hatchet-dev/typescript-sdk": "^1.5.0"
  },
  "devDependencies": {
    "tsx": "^4.19.0",
    "typescript": "^5.6.0"
  }
}
EOF

RUN cd /home/user/myproject && \
    npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet TypeScript SDK task environment for dynamic fan-out via child spawning (Node.js v24, tsx, @hatchet-dev/typescript-sdk pre-installed)."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 for the Hatchet TypeScript SDK task environment
#   - /home/user/myproject: TypeScript project directory
#   - /home/user/myproject/package.json: declares @hatchet-dev/typescript-sdk and tsx as dependencies
#   - /home/user/myproject/node_modules: pre-installed node modules including @hatchet-dev/typescript-sdk
