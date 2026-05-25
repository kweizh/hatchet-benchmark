FROM ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest AS hatchet-source

FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest python-is-python3 bash ripgrep \
        jq iproute2 procps sudo \
        musl \
        postgresql postgresql-contrib && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        pytest-xprocess \
        "hatchet-sdk>=1.0.0" \
        "pydantic>=2.0" \
        requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Bring in the prebuilt hatchet-lite, hatchet-admin and hatchet-migrate binaries plus the
# bundled static dashboard assets. The binaries are musl-linked Alpine binaries, so we
# install Ubuntu's musl libc package above and rely on /lib/ld-musl-<arch>.so.1 for loading.
RUN mkdir -p /opt/hatchet
COPY --from=hatchet-source /hatchet-lite /opt/hatchet/hatchet-lite
COPY --from=hatchet-source /hatchet-admin /opt/hatchet/hatchet-admin
COPY --from=hatchet-source /hatchet-migrate /opt/hatchet/hatchet-migrate
COPY --from=hatchet-source /static-assets /opt/hatchet/static-assets
RUN chmod +x /opt/hatchet/hatchet-lite /opt/hatchet/hatchet-admin /opt/hatchet/hatchet-migrate

# Create the user project directory.
RUN mkdir -p /home/user && chmod 0755 /home/user && \
    mkdir -p /home/user/project && chmod 0755 /home/user/project

# Auto-load /etc/hatchet.env into every Python process so the Hatchet SDK can
# pick up HATCHET_CLIENT_TOKEN without requiring the caller to source a profile.
# We use a .pth file (executed by `site.py` on interpreter startup) so it works
# even though the Ubuntu python3 package ships its own sitecustomize.py.
RUN install -d /usr/local/lib/python3.12/dist-packages && \
    cat >/usr/local/lib/python3.12/dist-packages/zealt_hatchet_env_loader.py <<'PY'
import os
from pathlib import Path


def _load() -> None:
    env_file = Path("/etc/hatchet.env")
    if not env_file.exists():
        return
    try:
        text = env_file.read_text()
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load()
PY
RUN cat >/usr/local/lib/python3.12/dist-packages/zealt_hatchet_env_loader.pth <<'PTH'
import zealt_hatchet_env_loader
PTH

# Init script: bootstraps Postgres, the local hatchet-lite engine, and generates
# a real HATCHET_CLIENT_TOKEN. Idempotent on container restart.
RUN cat >/usr/local/bin/init-hatchet.sh <<'SH' && chmod +x /usr/local/bin/init-hatchet.sh
#!/bin/bash
set -e

PG_BIN="/usr/lib/postgresql/16/bin"
PG_DATA="/var/lib/postgresql/data"
HATCHET_DIR="/opt/hatchet"
TENANT_ID="707d0855-80ab-4e1f-a156-f1c4546cbf52"

mkdir -p /var/log/hatchet
chmod 0777 /var/log/hatchet

# 1) Initialise Postgres cluster.
if [ ! -s "${PG_DATA}/PG_VERSION" ]; then
    rm -rf "${PG_DATA}"
    install -d -o postgres -g postgres -m 0700 "${PG_DATA}"
    su postgres -c "${PG_BIN}/initdb -D ${PG_DATA} --auth-local=trust --auth-host=trust --username=postgres" \
        >/var/log/hatchet/initdb.log 2>&1
    echo "listen_addresses = '127.0.0.1'" >> "${PG_DATA}/postgresql.conf"
    echo "max_connections = 200" >> "${PG_DATA}/postgresql.conf"
fi

# 2) Start Postgres.
su postgres -c "${PG_BIN}/pg_ctl -D ${PG_DATA} -l /var/log/hatchet/postgres.log -w start" \
    >/var/log/hatchet/pg_ctl.log 2>&1

# 3) Provision the Hatchet database/user (idempotent).
su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='hatchet'\"" | grep -q 1 || \
    su postgres -c "psql -c \"CREATE USER hatchet WITH PASSWORD 'hatchet';\""
su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='hatchet'\"" | grep -q 1 || \
    su postgres -c "psql -c \"CREATE DATABASE hatchet OWNER hatchet;\""

# 4) Set up Hatchet env (mirrors the official docker-compose.hatchet.yml).
export DATABASE_URL="postgresql://hatchet:hatchet@127.0.0.1:5432/hatchet?sslmode=disable"
export SERVER_AUTH_COOKIE_DOMAIN="localhost"
export SERVER_AUTH_COOKIE_INSECURE="t"
export SERVER_GRPC_BIND_ADDRESS="0.0.0.0"
export SERVER_GRPC_INSECURE="t"
export SERVER_GRPC_BROADCAST_ADDRESS="127.0.0.1:7077"
export SERVER_GRPC_PORT="7077"
export SERVER_URL="http://127.0.0.1:8888"
export SERVER_AUTH_SET_EMAIL_VERIFIED="t"
export SERVER_DEFAULT_ENGINE_VERSION="V1"
export SERVER_INTERNAL_CLIENT_INTERNAL_GRPC_BROADCAST_ADDRESS="127.0.0.1:7077"
export LITE_STATIC_ASSET_DIR="/opt/hatchet/static-assets"
export LITE_FRONTEND_PORT="8888"

cd "${HATCHET_DIR}"

# 5) Run migrations and generate the engine config (idempotent with --overwrite=false).
./hatchet-migrate >>/var/log/hatchet/migrate.log 2>&1
./hatchet-admin quickstart --skip certs --generated-config-dir ./config --overwrite=false \
    >>/var/log/hatchet/quickstart.log 2>&1 || true

# 6) Start hatchet-lite if not already running.
if ! pgrep -x hatchet-lite >/dev/null 2>&1; then
    nohup ./hatchet-lite --config ./config >>/var/log/hatchet/hatchet-lite.log 2>&1 &
fi

# 7) Wait for the gRPC port to come up.
for _ in $(seq 1 90); do
    if ss -tnlp 2>/dev/null | grep -q ':7077'; then
        break
    fi
    sleep 2
done

# 8) Generate the API token for the default tenant.
TOKEN=""
for _ in $(seq 1 30); do
    TOKEN=$(./hatchet-admin token create --config ./config --tenant-id "${TENANT_ID}" --name local 2>/var/log/hatchet/token.err | tr -d '[:space:]' || true)
    if [ -n "${TOKEN}" ] && [ "${#TOKEN}" -gt 50 ]; then
        break
    fi
    sleep 2
done

if [ -z "${TOKEN}" ] || [ "${#TOKEN}" -lt 50 ]; then
    echo "ERROR: failed to generate HATCHET_CLIENT_TOKEN" >&2
    cat /var/log/hatchet/token.err >&2 || true
    exit 1
fi

# 9) Persist the env so every shell / Python process inherits it.
umask 022
cat >/etc/hatchet.env.tmp <<EOF
HATCHET_CLIENT_TOKEN=${TOKEN}
HATCHET_CLIENT_TLS_STRATEGY=none
HATCHET_CLIENT_HOST_PORT=127.0.0.1:7077
EOF
mv /etc/hatchet.env.tmp /etc/hatchet.env

cat >/etc/profile.d/hatchet.sh <<EOF
export HATCHET_CLIENT_TOKEN="${TOKEN}"
export HATCHET_CLIENT_TLS_STRATEGY="none"
export HATCHET_CLIENT_HOST_PORT="127.0.0.1:7077"
EOF
chmod 0644 /etc/profile.d/hatchet.sh

echo "hatchet-lite bootstrap complete; token length=${#TOKEN}" >&2
SH

LABEL Author="generate-harbor-tasks"
LABEL Description="Hatchet wait-for-event durable task environment: ubuntu:24.04 with local hatchet-lite + Postgres, hatchet-sdk preinstalled, real HATCHET_CLIENT_TOKEN bootstrapped on container start."

CMD ["/bin/bash", "-c", "/usr/local/bin/init-hatchet.sh && trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - extra apt packages: jq iproute2 procps sudo musl postgresql postgresql-contrib
#   - extra pip packages: hatchet-sdk, pytest-xprocess, pydantic, requests (for SDK and verifier)
#   - /opt/hatchet/{hatchet-lite,hatchet-admin,hatchet-migrate}: musl-linked Hatchet binaries
#     copied from the official ghcr.io/hatchet-dev/hatchet/hatchet-lite image
#   - /usr/local/lib/python3.12/dist-packages/zealt_hatchet_env_loader.*: auto-loads /etc/hatchet.env
#   - /usr/local/bin/init-hatchet.sh: bootstraps Postgres + hatchet-lite + HATCHET_CLIENT_TOKEN
#   - /home/user/project: empty directory where the user will create worker.py and trigger.py
