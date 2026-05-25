###############################################################################
# Stage 1: pull binaries from the official hatchet-lite image
###############################################################################
FROM ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest AS hatchet-bin

###############################################################################
# Stage 2: ubuntu-based runtime that bundles postgres + hatchet-lite + python
###############################################################################
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PG_VERSION=16
ENV PG_BIN=/usr/lib/postgresql/16/bin
ENV PG_DATA=/var/lib/postgresql/16/main

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        postgresql-16 postgresql-client-16 sudo procps net-tools tini \
        musl && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        pytest-xprocess \
        hatchet-sdk \
        python-dotenv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the prebuilt Hatchet binaries plus the dashboard static assets from the
# official lite image.
COPY --from=hatchet-bin /hatchet-lite /usr/local/bin/hatchet-lite
COPY --from=hatchet-bin /hatchet-admin /usr/local/bin/hatchet-admin
COPY --from=hatchet-bin /hatchet-migrate /usr/local/bin/hatchet-migrate
COPY --from=hatchet-bin /static-assets /static-assets
RUN chmod +x /usr/local/bin/hatchet-lite /usr/local/bin/hatchet-admin /usr/local/bin/hatchet-migrate

ENV LITE_STATIC_ASSET_DIR=/static-assets \
    LITE_FRONTEND_PORT=8081 \
    LITE_RUNTIME_PORT=8888

# Configuration the Hatchet server reads from environment variables at every
# invocation (both the build-time bootstrap below and the runtime entrypoint).
ENV DATABASE_URL="postgresql://hatchet:hatchet@127.0.0.1:5432/hatchet?sslmode=disable" \
    SERVER_AUTH_COOKIE_DOMAIN=localhost \
    SERVER_AUTH_COOKIE_INSECURE=t \
    SERVER_GRPC_BIND_ADDRESS=0.0.0.0 \
    SERVER_GRPC_INSECURE=t \
    SERVER_GRPC_BROADCAST_ADDRESS=localhost:7077 \
    SERVER_GRPC_PORT=7077 \
    SERVER_URL=http://localhost:8888 \
    SERVER_AUTH_SET_EMAIL_VERIFIED=t \
    SERVER_DEFAULT_ENGINE_VERSION=V1 \
    SERVER_INTERNAL_CLIENT_INTERNAL_GRPC_BROADCAST_ADDRESS=localhost:7077 \
    HATCHET_CLIENT_HOST_PORT=localhost:7077 \
    HATCHET_CLIENT_TLS_STRATEGY=none

# Bootstrap postgres + hatchet-lite at image-build time so that a real API token
# can be embedded into the image. The token is signed against the secrets in
# /hatchet-config, so as long as that directory and the postgres data dir
# persist (they do, since this RUN is captured as image layers) the token is
# valid every time the container is restarted.
RUN set -e && \
    mkdir -p /etc/zealt /hatchet-config /var/run/postgresql /var/log/postgresql && \
    chown postgres:postgres /var/run/postgresql /var/log/postgresql && \
    chown -R postgres:postgres /var/lib/postgresql && \
    pg_ctlcluster ${PG_VERSION} main start && \
    su postgres -c "psql -v ON_ERROR_STOP=1 -c \"CREATE USER hatchet WITH PASSWORD 'hatchet';\"" && \
    su postgres -c "psql -v ON_ERROR_STOP=1 -c \"CREATE DATABASE hatchet OWNER hatchet;\"" && \
    su postgres -c "psql -v ON_ERROR_STOP=1 -d hatchet -c \"GRANT ALL ON SCHEMA public TO hatchet;\"" && \
    hatchet-migrate && \
    hatchet-admin quickstart --skip certs --generated-config-dir /hatchet-config --overwrite=false && \
    HATCHET_TOKEN="$(hatchet-admin token create --config /hatchet-config --tenant-id 707d0855-80ab-4e1f-a156-f1c4546cbf52 | tr -d '[:space:]')" && \
    test -n "$HATCHET_TOKEN" && \
    printf 'HATCHET_CLIENT_TOKEN=%s\nHATCHET_CLIENT_HOST_PORT=localhost:7077\nHATCHET_CLIENT_TLS_STRATEGY=none\n' "$HATCHET_TOKEN" > /etc/zealt/hatchet.env && \
    printf 'export HATCHET_CLIENT_TOKEN=%s\nexport HATCHET_CLIENT_HOST_PORT=localhost:7077\nexport HATCHET_CLIENT_TLS_STRATEGY=none\n' "$HATCHET_TOKEN" > /etc/zealt/hatchet.sh && \
    chmod 0644 /etc/zealt/hatchet.env /etc/zealt/hatchet.sh && \
    pg_ctlcluster ${PG_VERSION} main stop -- -m fast && \
    head -c 80 /etc/zealt/hatchet.env && echo

# Make sure every non-interactive bash shell (including the one Harbor spawns
# for tests) sees HATCHET_CLIENT_TOKEN / HATCHET_CLIENT_HOST_PORT.
ENV BASH_ENV=/etc/zealt/hatchet.sh
RUN cp /etc/zealt/hatchet.sh /etc/profile.d/zealt-hatchet.sh && \
    echo "source /etc/zealt/hatchet.sh" >> /etc/bash.bashrc

# Runtime entrypoint: start postgres and hatchet-lite, then keep the container
# alive. Also expose the bootstrapped HATCHET_CLIENT_TOKEN to subsequent
# `docker exec` sessions via /etc/zealt/hatchet.sh (already loaded via
# BASH_ENV).
RUN printf '%s\n' \
    '#!/bin/bash' \
    'set -e' \
    '' \
    'mkdir -p /var/run/postgresql /var/log/postgresql' \
    'chown postgres:postgres /var/run/postgresql /var/log/postgresql' \
    '' \
    '# Start postgres' \
    'pg_ctlcluster ${PG_VERSION} main start' \
    '' \
    '# Start hatchet-lite in background' \
    'nohup hatchet-lite --config /hatchet-config >/var/log/hatchet-lite.log 2>&1 &' \
    '' \
    '# Wait until hatchet-lite is accepting gRPC connections.' \
    'for i in $(seq 1 90); do' \
    '  if (echo > /dev/tcp/127.0.0.1/7077) 2>/dev/null; then' \
    '    echo "hatchet-lite ready on :7077"' \
    '    break' \
    '  fi' \
    '  sleep 1' \
    'done' \
    '' \
    'echo "zealt-startup complete"' \
    > /usr/local/bin/zealt-startup.sh && \
    chmod +x /usr/local/bin/zealt-startup.sh

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/myproject

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet bulk-trigger (Python) task environment: ubuntu:24.04 with PostgreSQL 16, a self-hosted hatchet-lite engine, hatchet-sdk for Python, and a pre-bootstrapped HATCHET_CLIENT_TOKEN."

CMD ["/bin/bash", "-lc", "/usr/local/bin/zealt-startup.sh && trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - PostgreSQL 16 (server + client) pre-initialized with a `hatchet` user/db
#   - Hatchet binaries from ghcr.io/hatchet-dev/hatchet/hatchet-lite:
#       /usr/local/bin/hatchet-lite, /usr/local/bin/hatchet-admin, /usr/local/bin/hatchet-migrate
#   - /hatchet-config: prebuilt hatchet-lite config (keys, default tenant, etc.)
#   - /etc/zealt/hatchet.env: HATCHET_CLIENT_TOKEN / HATCHET_CLIENT_HOST_PORT in dotenv format
#   - /etc/zealt/hatchet.sh: same values as `export` statements; sourced via BASH_ENV
#   - /usr/local/bin/zealt-startup.sh: starts postgres + hatchet-lite at container boot
#   - hatchet-sdk + pytest-xprocess + python-dotenv installed for both task execution and verification
#   - /home/user/myproject: empty project directory where the agent builds the bulk-trigger script
