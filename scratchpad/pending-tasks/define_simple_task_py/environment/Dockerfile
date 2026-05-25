# NOTE on base image:
# The general rule is to use ubuntu:24.04 as the base image, but this task
# explicitly requires running `ghcr.io/hatchet-dev/hatchet/hatchet-lite` and
# `postgres:15.6` as background services inside a single container. The
# hatchet-lite binary is built on Alpine (musl libc), so we use the
# alpine-based `postgres:15.6-alpine` image as the final base and copy the
# hatchet binaries directly from the official `hatchet-lite` image to
# guarantee binary compatibility with musl. Both required images are
# materialised below as multi-stage sources.

FROM ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest AS hatchet-source
FROM postgres:15.6 AS postgres-debian-source

FROM postgres:15.6-alpine

# ---------------------------------------------------------------------------
# Install system packages, Python, supervisor, and miscellaneous tooling.
# Alpine's python3 is PEP-668 protected, so we keep the venv pattern.
# ---------------------------------------------------------------------------
RUN apk update && apk add --no-cache \
        bash \
        curl \
        wget \
        ca-certificates \
        git \
        ripgrep \
        python3 \
        py3-pip \
        py3-virtualenv \
        supervisor \
        netcat-openbsd \
        procps \
        shadow \
        coreutils \
        tini

# ---------------------------------------------------------------------------
# Copy hatchet binaries from the official hatchet-lite image. The binaries
# expected by hatchet-lite's own entrypoint live at /hatchet-lite,
# /hatchet-admin, /hatchet-migrate and /static-assets.
# ---------------------------------------------------------------------------
COPY --from=hatchet-source /hatchet-lite      /usr/local/bin/hatchet-lite
COPY --from=hatchet-source /hatchet-admin     /usr/local/bin/hatchet-admin
COPY --from=hatchet-source /hatchet-migrate   /usr/local/bin/hatchet-migrate
COPY --from=hatchet-source /static-assets     /static-assets

RUN chmod +x /usr/local/bin/hatchet-lite \
             /usr/local/bin/hatchet-admin \
             /usr/local/bin/hatchet-migrate

# ---------------------------------------------------------------------------
# Set up a Python virtual environment with the libraries needed both by the
# task executor and by the verifier (hatchet-sdk, pydantic, pytest, etc.).
# ---------------------------------------------------------------------------
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir \
        hatchet-sdk \
        pydantic \
        pytest \
        pytest-xprocess \
        pytest-json-ctrf \
        requests
ENV PATH=/opt/venv/bin:$PATH

# ---------------------------------------------------------------------------
# Prepare /home/user and the working project directory.
# ---------------------------------------------------------------------------
RUN mkdir -p /home/user && chmod 0755 /home/user && \
    mkdir -p /home/user/myproject && chmod 0755 /home/user/myproject

# ---------------------------------------------------------------------------
# Configure PostgreSQL data directory. We let the postgres:15.6-alpine
# image's entrypoint conventions remain, but run postgres directly through
# our start script. PostgreSQL must run as the `postgres` user.
# `initdb` refuses to run unless PGDATA has 0700 permissions, so make sure
# the directory is empty and properly owned and chmod'd here.
# ---------------------------------------------------------------------------
ENV PGDATA=/var/lib/postgresql/data
RUN rm -rf "$PGDATA" && \
    mkdir -p "$PGDATA" /var/run/postgresql /config && \
    chown -R postgres:postgres "$PGDATA" /var/run/postgresql /config && \
    chmod 0700 "$PGDATA"

# ---------------------------------------------------------------------------
# Startup script: initialises postgres, starts postgres + hatchet-lite, then
# mints a real Hatchet API token using hatchet-admin and exports it via a
# globally sourced env file so both interactive shells and the verifier see
# `HATCHET_CLIENT_TOKEN`.
# ---------------------------------------------------------------------------
RUN cat >/usr/local/bin/start-services.sh <<'EOF'
#!/usr/bin/env bash
# Best-effort orchestration script. We do NOT use `set -e` here so a single
# transient failure (e.g. an existing database) does not kill the container.
set -u

ZEALT_ENV_FILE=/etc/zealt-env.sh
TENANT_ID="707d0855-80ab-4e1f-a156-f1c4546cbf52"

log() { echo "[start-services] $*"; }

# ---- 1. PostgreSQL ---------------------------------------------------------
# Ensure the data directory has correct ownership and 0700 permissions
# regardless of how it was created.
chown -R postgres:postgres "$PGDATA"
chmod 0700 "$PGDATA"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    log "Initialising PostgreSQL data directory at $PGDATA"
    # initdb will not work if PGDATA contains any files (it does a "directory
    # not empty" check). Wipe stale leftovers (everything is recreated).
    find "$PGDATA" -mindepth 1 -delete
    PWFILE=/tmp/pg-superuser-password
    echo "hatchet" > "$PWFILE"
    chown postgres:postgres "$PWFILE"
    chmod 0600 "$PWFILE"
    su-exec postgres initdb -D "$PGDATA" \
        --username=postgres \
        --pwfile="$PWFILE" >/var/log/initdb.log 2>&1
    INITDB_RC=$?
    rm -f "$PWFILE"
    if [ "$INITDB_RC" -ne 0 ]; then
        log "ERROR: initdb failed (exit $INITDB_RC); see /var/log/initdb.log"
        cat /var/log/initdb.log || true
        exit 1
    fi
    echo "host all all 127.0.0.1/32 md5"  >> "$PGDATA/pg_hba.conf"
    echo "host all all ::1/128       md5" >> "$PGDATA/pg_hba.conf"
    echo "listen_addresses = 'localhost'" >> "$PGDATA/postgresql.conf"
fi

log "Starting PostgreSQL"
su-exec postgres postgres -D "$PGDATA" >/var/log/postgres.log 2>&1 &
POSTGRES_PID=$!

# Wait for postgres to accept connections
for i in $(seq 1 60); do
    if su-exec postgres pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        log "PostgreSQL is ready"
        break
    fi
    sleep 1
done

# Create the hatchet role / db if missing
if ! su-exec postgres psql -h localhost -U postgres -tAc \
        "SELECT 1 FROM pg_roles WHERE rolname='hatchet'" 2>/dev/null | grep -q 1; then
    su-exec postgres psql -h localhost -U postgres -c \
        "CREATE ROLE hatchet WITH LOGIN SUPERUSER PASSWORD 'hatchet';" \
        >/var/log/pg-role.log 2>&1 || \
        log "WARN: failed to create hatchet role; see /var/log/pg-role.log"
fi
if ! su-exec postgres psql -h localhost -U postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname='hatchet'" 2>/dev/null | grep -q 1; then
    su-exec postgres createdb -h localhost -U postgres -O hatchet hatchet \
        >/var/log/pg-db.log 2>&1 || \
        log "WARN: failed to create hatchet db; see /var/log/pg-db.log"
fi

# ---- 2. Hatchet ------------------------------------------------------------
export DATABASE_URL="postgresql://hatchet:hatchet@localhost:5432/hatchet?sslmode=disable"
export SERVER_AUTH_COOKIE_DOMAIN=localhost
export SERVER_AUTH_COOKIE_INSECURE=t
export SERVER_GRPC_BIND_ADDRESS=0.0.0.0
export SERVER_GRPC_INSECURE=t
export SERVER_GRPC_BROADCAST_ADDRESS=localhost:7077
export SERVER_GRPC_PORT=7077
export SERVER_URL=http://localhost:8888
export SERVER_AUTH_SET_EMAIL_VERIFIED=t
export SERVER_DEFAULT_ENGINE_VERSION=V1
export SERVER_INTERNAL_CLIENT_INTERNAL_GRPC_BROADCAST_ADDRESS=localhost:7077
export LITE_STATIC_ASSET_DIR=/static-assets
export LITE_FRONTEND_PORT=8081
export LITE_RUNTIME_PORT=8888

log "Running hatchet-migrate"
hatchet-migrate >/var/log/hatchet-migrate.log 2>&1 || \
    log "hatchet-migrate exited non-zero (may be idempotent); continuing"

log "Generating hatchet config"
hatchet-admin quickstart --skip certs --generated-config-dir /config --overwrite=false \
    >/var/log/hatchet-quickstart.log 2>&1 || \
    log "hatchet-admin quickstart exited non-zero (may already be configured); continuing"

log "Starting hatchet-lite"
hatchet-lite --config /config >/var/log/hatchet-lite.log 2>&1 &
HATCHET_PID=$!

# Wait for gRPC + HTTP API to come up.
for i in $(seq 1 120); do
    if nc -z localhost 7077 && nc -z localhost 8888; then
        log "hatchet-lite is ready"
        break
    fi
    sleep 1
done

# Mint a real API token for clients.
log "Creating Hatchet API token"
TOKEN=""
for i in $(seq 1 20); do
    TOKEN=$(hatchet-admin token create \
        --config /config \
        --tenant-id "$TENANT_ID" \
        --name "zealt-default" 2>/var/log/hatchet-token.err | tail -n 1 | tr -d '[:space:]') || true
    if [ -n "$TOKEN" ] && [ "${#TOKEN}" -gt 20 ]; then
        break
    fi
    log "Token creation attempt $i failed; retrying..."
    sleep 2
done

if [ -z "$TOKEN" ]; then
    log "ERROR: failed to create Hatchet API token; see /var/log/hatchet-token.err"
    log "$(cat /var/log/hatchet-token.err 2>/dev/null || true)"
fi

# Publish env vars so user shells and the verifier all see them.
{
    echo "export PATH=/opt/venv/bin:\$PATH"
    echo "export HATCHET_CLIENT_TOKEN='$TOKEN'"
    echo "export HATCHET_CLIENT_TLS_STRATEGY=none"
    echo "export HATCHET_CLIENT_HOST_PORT=localhost:7077"
    echo "export HATCHET_CLIENT_SERVER_URL=http://localhost:8888"
    echo "export HATCHET_CLIENT_NAMESPACE=default"
} > "$ZEALT_ENV_FILE"
chmod 0644 "$ZEALT_ENV_FILE"

mkdir -p /etc/profile.d
cp "$ZEALT_ENV_FILE" /etc/profile.d/zealt-env.sh

# Make the env file available to non-login shells via BASH_ENV-style sourcing.
grep -q "zealt-env.sh" /etc/bash.bashrc 2>/dev/null || \
    echo ". /etc/zealt-env.sh" >> /etc/bash.bashrc
touch /root/.bashrc /home/user/.bashrc 2>/dev/null || true
grep -q "zealt-env.sh" /root/.bashrc 2>/dev/null || \
    echo ". /etc/zealt-env.sh" >> /root/.bashrc
grep -q "zealt-env.sh" /home/user/.bashrc 2>/dev/null || \
    echo ". /etc/zealt-env.sh" >> /home/user/.bashrc

log "Hatchet stack ready. HATCHET_CLIENT_TOKEN length=${#TOKEN}"

# Keep PID 1 alive while the background services run.
wait $HATCHET_PID
EOF
RUN chmod +x /usr/local/bin/start-services.sh

# ---------------------------------------------------------------------------
# Configure global env file early so initial-state tests can find it even
# before the startup script has fully run (the file is rewritten with the
# real token at runtime).
# ---------------------------------------------------------------------------
RUN echo "export PATH=/opt/venv/bin:\$PATH" > /etc/zealt-env.sh && \
    echo "export HATCHET_CLIENT_TLS_STRATEGY=none" >> /etc/zealt-env.sh && \
    echo "export HATCHET_CLIENT_HOST_PORT=localhost:7077" >> /etc/zealt-env.sh && \
    echo "export HATCHET_CLIENT_SERVER_URL=http://localhost:8888" >> /etc/zealt-env.sh && \
    mkdir -p /etc/profile.d && \
    cp /etc/zealt-env.sh /etc/profile.d/zealt-env.sh && \
    echo ". /etc/zealt-env.sh" >> /etc/bash.bashrc

# Ensure BASH_ENV is set so non-interactive bash shells (e.g. the harness
# `bash -c` invocations) source the env file and pick up the token.
ENV BASH_ENV=/etc/zealt-env.sh
ENV ENV=/etc/zealt-env.sh

LABEL Author="generate-harbor-tasks"
LABEL Description="Self-contained Hatchet Lite + PostgreSQL 15.6 + Python 3 environment for the define_simple_task_py task."

EXPOSE 7077 8888

# Boot the postgres + hatchet stack via tini so signals propagate properly.
# The startup script blocks on the hatchet-lite process so PID 1 remains
# alive for the lifetime of the container.
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/start-services.sh"]

# Container contents:
#   - postgres:15.6-alpine (final base, runs postgres as a background service)
#   - hatchet binaries (hatchet-lite, hatchet-admin, hatchet-migrate, static
#     assets) copied from ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest
#   - Python 3 venv at /opt/venv with hatchet-sdk, pydantic, pytest,
#     pytest-xprocess, pytest-json-ctrf, requests
#   - Always-required apt-equivalent packages (curl, wget, ca-certificates,
#     git, ripgrep, bash, netcat) installed via apk
#   - /usr/local/bin/start-services.sh -- orchestrates postgres + hatchet
#     and mints a real HATCHET_CLIENT_TOKEN at runtime
#   - /etc/zealt-env.sh -- runtime env file sourced from bashrc/profile/BASH_ENV
#   - /home/user/myproject -- working directory for the user's worker.py
