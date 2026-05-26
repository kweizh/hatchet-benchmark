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

# Set up a minimal Node.js project pre-installed with the Hatchet TypeScript SDK
# and tsx so the executor can immediately implement worker.ts and run.ts.
RUN mkdir -p /home/user/myproject && \
    cd /home/user/myproject && \
    cat >package.json <<'PKGJSON'
{
  "name": "linear-dag-ts",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "worker": "tsx src/worker.ts",
    "run": "tsx src/run.ts"
  },
  "dependencies": {
    "@hatchet-dev/typescript-sdk": "latest"
  },
  "devDependencies": {
    "tsx": "latest",
    "typescript": "latest"
  }
}
PKGJSON

RUN cd /home/user/myproject && \
    cat >tsconfig.json <<'TSCONF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "strict": false,
    "skipLibCheck": true,
    "allowImportingTsExtensions": false,
    "noEmit": true
  },
  "include": ["src/**/*.ts"]
}
TSCONF

RUN cd /home/user/myproject && \
    mkdir -p src && \
    npm install --no-audit --no-fund --loglevel=error

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet TypeScript SDK linear DAG task environment with Node.js v24 and @hatchet-dev/typescript-sdk pre-installed."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 for running TypeScript via tsx
#   - /home/user/myproject: Node project pre-configured with package.json, tsconfig.json,
#     and @hatchet-dev/typescript-sdk + tsx installed in node_modules
