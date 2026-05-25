FROM ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest AS hatchet-lite

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PGDATA=/var/lib/postgresql/data
ENV HATCHET_CONFIG_DIR=/opt/hatchet/config
ENV HATCHET_TENANT_ID=707d0855-80ab-4e1f-a156-f1c4546cbf52
ENV HATCHET_CLIENT_TLS_STRATEGY=none
ENV HATCHET_CLIENT_TENANT_ID=707d0855-80ab-4e1f-a156-f1c4546cbf52
ENV HATCHET_CLIENT_HOST_PORT=localhost:7077
ENV BASH_ENV=/etc/hatchet.env

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        postgresql postgresql-contrib gnupg lsb-release procps net-tools jq sudo tini \
        musl tzdata openssl && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages \
        pytest-json-ctrf pytest-xprocess requests hatchet-sdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy hatchet binaries and static assets from the official hatchet-lite image.
COPY --from=hatchet-lite /hatchet-lite /usr/local/bin/hatchet-lite
COPY --from=hatchet-lite /hatchet-admin /usr/local/bin/hatchet-admin
COPY --from=hatchet-lite /hatchet-migrate /usr/local/bin/hatchet-migrate
COPY --from=hatchet-lite /static-assets /opt/hatchet/static-assets

RUN chmod +x /usr/local/bin/hatchet-lite /usr/local/bin/hatchet-admin /usr/local/bin/hatchet-migrate && \
    mkdir -p /opt/hatchet/config /var/log/hatchet && \
    chown -R postgres:postgres /var/log/hatchet

# Prepare PostgreSQL data directory and ensure the cluster is initialised at build time
# so first start-up only needs to launch postgres.
RUN mkdir -p ${PGDATA} && chown -R postgres:postgres ${PGDATA} && \
    su postgres -c "/usr/lib/postgresql/16/bin/initdb -D ${PGDATA} --auth=trust --username=postgres" && \
    echo "host all all 127.0.0.1/32 trust" >> ${PGDATA}/pg_hba.conf && \
    echo "listen_addresses = 'localhost'" >> ${PGDATA}/postgresql.conf

# Seed /etc/hatchet.env so BASH_ENV does not fail before start-hatchet.sh runs.
RUN printf "%s\n" \
    "# This file is rewritten at container startup by /usr/local/bin/start-hatchet.sh" \
    "export HATCHET_CLIENT_TLS_STRATEGY=none" \
    "export HATCHET_CLIENT_TENANT_ID=707d0855-80ab-4e1f-a156-f1c4546cbf52" \
    "export HATCHET_CLIENT_HOST_PORT=localhost:7077" \
    > /etc/hatchet.env && chmod 0644 /etc/hatchet.env && \
    echo '. /etc/hatchet.env' >> /etc/bash.bashrc && \
    echo '. /etc/hatchet.env' >> /root/.bashrc

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/myproject && chmod 0755 /home/user/myproject

# Startup script: brings up postgres + hatchet-lite, creates a real
# HATCHET_CLIENT_TOKEN via the hatchet-admin CLI, then sleeps to keep the
# container alive for the agent and the verifier.
RUN cat > /usr/local/bin/start-hatchet.sh <<'STARTSH'
#!/usr/bin/env bash
# shellcheck disable=SC2155

LOG_DIR=/var/log/hatchet
mkdir -p "$LOG_DIR"

echo "[start-hatchet] launching postgres..." | tee -a "$LOG_DIR/start.log"
su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D ${PGDATA} -l ${LOG_DIR}/postgres.log start" \
  || echo "[start-hatchet] postgres pg_ctl exited (may already be running)" | tee -a "$LOG_DIR/start.log"

# Wait for postgres to accept connections.
for i in $(seq 1 60); do
  if su postgres -c "psql -U postgres -h localhost -d postgres -c 'SELECT 1' >/dev/null 2>&1"; then
    break
  fi
  sleep 0.5
done

echo "[start-hatchet] ensuring hatchet role and database..." | tee -a "$LOG_DIR/start.log"
su postgres -c "psql -U postgres -h localhost -d postgres -tAc \"SELECT 1 FROM pg_roles WHERE rolname='hatchet'\"" \
  | grep -q 1 \
  || su postgres -c "psql -U postgres -h localhost -d postgres -c \"CREATE ROLE hatchet WITH LOGIN SUPERUSER PASSWORD 'hatchet'\""
su postgres -c "psql -U postgres -h localhost -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='hatchet'\"" \
  | grep -q 1 \
  || su postgres -c "psql -U postgres -h localhost -d postgres -c \"CREATE DATABASE hatchet OWNER hatchet\""

export DATABASE_URL="postgresql://hatchet:hatchet@localhost:5432/hatchet?sslmode=disable"
export SERVER_AUTH_COOKIE_DOMAIN=localhost
export SERVER_AUTH_COOKIE_INSECURE=t
export SERVER_GRPC_BIND_ADDRESS=0.0.0.0
export SERVER_GRPC_INSECURE=t
export SERVER_GRPC_BROADCAST_ADDRESS=localhost:7077
export SERVER_GRPC_PORT=7077
export SERVER_PORT=8080
export SERVER_URL=http://localhost:8888
export SERVER_AUTH_SET_EMAIL_VERIFIED=t
export SERVER_DEFAULT_ENGINE_VERSION=V1
export SERVER_INTERNAL_CLIENT_INTERNAL_GRPC_BROADCAST_ADDRESS=localhost:7077
export LITE_STATIC_ASSET_DIR=/opt/hatchet/static-assets
export LITE_FRONTEND_PORT=8081
export LITE_RUNTIME_PORT=8888

cd /opt/hatchet

echo "[start-hatchet] running hatchet-migrate..." | tee -a "$LOG_DIR/start.log"
/usr/local/bin/hatchet-migrate >>"$LOG_DIR/migrate.log" 2>&1 || {
  echo "[start-hatchet] hatchet-migrate failed; see $LOG_DIR/migrate.log" | tee -a "$LOG_DIR/start.log"
  exit 1
}

echo "[start-hatchet] generating hatchet config..." | tee -a "$LOG_DIR/start.log"
/usr/local/bin/hatchet-admin quickstart --skip certs --generated-config-dir "$HATCHET_CONFIG_DIR" --overwrite=false >>"$LOG_DIR/quickstart.log" 2>&1 || true

echo "[start-hatchet] starting hatchet-lite engine..." | tee -a "$LOG_DIR/start.log"
nohup /usr/local/bin/hatchet-lite --config "$HATCHET_CONFIG_DIR" >>"$LOG_DIR/hatchet-lite.log" 2>&1 &

# Wait for the API server and gRPC port to be ready.
for i in $(seq 1 120); do
  if curl -fsS -o /dev/null "http://localhost:8888/api/v1/meta" && \
     bash -c "</dev/tcp/127.0.0.1/7077" >/dev/null 2>&1 ; then
    echo "[start-hatchet] engine ready after ${i}s" | tee -a "$LOG_DIR/start.log"
    break
  fi
  sleep 1
done

echo "[start-hatchet] minting HATCHET_CLIENT_TOKEN via hatchet-admin..." | tee -a "$LOG_DIR/start.log"
TOKEN_OUTPUT="$(/usr/local/bin/hatchet-admin token create --config "$HATCHET_CONFIG_DIR" --tenant-id "$HATCHET_TENANT_ID" --name harbor-default 2>>"$LOG_DIR/token.log")"
TOKEN_VALUE="$(echo "$TOKEN_OUTPUT" | tr -d '\r' | awk 'NF{line=$0} END{print line}')"

if [ -z "$TOKEN_VALUE" ]; then
  echo "[start-hatchet] FAILED to obtain Hatchet client token. See $LOG_DIR/token.log" | tee -a "$LOG_DIR/start.log"
  exit 1
fi

cat > /etc/hatchet.env <<ENV
# Auto-generated by /usr/local/bin/start-hatchet.sh at container startup.
export HATCHET_CLIENT_TOKEN="$TOKEN_VALUE"
export HATCHET_CLIENT_TLS_STRATEGY=none
export HATCHET_CLIENT_TENANT_ID="$HATCHET_TENANT_ID"
export HATCHET_CLIENT_HOST_PORT=localhost:7077
ENV
chmod 0644 /etc/hatchet.env

echo "[start-hatchet] HATCHET_CLIENT_TOKEN written to /etc/hatchet.env" | tee -a "$LOG_DIR/start.log"

# Keep the container alive while honouring SIGTERM/SIGINT.
trap 'echo "[start-hatchet] shutting down"; exit 0' TERM INT
sleep infinity & wait
STARTSH

RUN chmod +x /usr/local/bin/start-hatchet.sh

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet Lite + PostgreSQL self-hosted environment with Node.js 22, the Hatchet TypeScript SDK runtime, and the Python hatchet-sdk verifier."

EXPOSE 7077 8888

CMD ["/usr/bin/tini", "--", "/usr/local/bin/start-hatchet.sh"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Self-hosted Hatchet Lite engine: hatchet-lite, hatchet-admin, hatchet-migrate copied from ghcr.io/hatchet-dev/hatchet/hatchet-lite
#   - PostgreSQL 16 (pre-initialised cluster at /var/lib/postgresql/data) as the Hatchet engine datastore
#   - Node.js 22 (LTS) and npm for the @hatchet-dev/typescript-sdk worker that the agent writes
#   - Python hatchet-sdk + pytest-xprocess + requests for the verifier to trigger workflows
#   - /usr/local/bin/start-hatchet.sh: container entrypoint that boots postgres, runs migrations, launches hatchet-lite, and mints a real HATCHET_CLIENT_TOKEN via `hatchet-admin token create`
#   - /etc/hatchet.env: runtime-written file containing the real HATCHET_CLIENT_TOKEN; sourced via BASH_ENV and /etc/bash.bashrc
#   - /home/user/myproject: working directory for the agent
