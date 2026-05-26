FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g pnpm@9 tsx@4 && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# Bootstrap the TypeScript project for the executor: a package.json with
# scripts and the @hatchet-dev/typescript-sdk dependency already installed.
RUN mkdir -p /home/user/myproject/src && \
    cd /home/user/myproject && \
    cat >package.json <<'JSON'
{
  "name": "concurrency-limit-ts",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "worker": "tsx src/worker.ts",
    "runner": "tsx src/runner.ts"
  },
  "dependencies": {
    "@hatchet-dev/typescript-sdk": "^1.0.0"
  },
  "devDependencies": {
    "tsx": "^4.19.0",
    "typescript": "^5.5.0"
  }
}
JSON
RUN cd /home/user/myproject && \
    cat >tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*.ts"]
}
JSON
RUN cd /home/user/myproject && \
    pnpm install --prod=false

LABEL Author="generate-harbor-tasks"
LABEL Description="Node.js v24 environment with @hatchet-dev/typescript-sdk and tsx pre-installed for a Hatchet TypeScript concurrency task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 with global pnpm and tsx
#   - /home/user/myproject: TypeScript project with @hatchet-dev/typescript-sdk installed
#   - package.json scripts: `pnpm run worker` and `pnpm run runner`
