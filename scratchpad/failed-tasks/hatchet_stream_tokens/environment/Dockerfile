FROM ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest AS hatchet-bins

FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash postgresql postgresql-contrib && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk==0.45.0

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /opt/hatchet && \
    mkdir -p /opt/hatchet/config

COPY --from=hatchet-bins /hatchet-lite /opt/hatchet/hatchet-lite
COPY --from=hatchet-bins /hatchet-admin /opt/hatchet/hatchet-admin
COPY --from=hatchet-bins /hatchet-migrate /opt/hatchet/hatchet-migrate
COPY --from=hatchet-bins /static-assets /opt/hatchet/static-assets

RUN /etc/init.d/postgresql start && \
    su - postgres -c "psql --command \"CREATE USER hatchet WITH SUPERUSER PASSWORD 'hatchet';\"" && \
    su - postgres -c "createdb -O hatchet hatchet"

RUN curl -fsSL https://install.hatchet.run/install.sh | bash

RUN cat > /usr/local/bin/start-hatchet.sh <<'EOF'
#!/bin/bash
/etc/init.d/postgresql start

until su - postgres -c "pg_isready" >/dev/null 2>&1; do
  sleep 1
done

export DATABASE_URL="postgresql://hatchet:hatchet@127.0.0.1:5432/hatchet?sslmode=disable"
export SERVER_AUTH_COOKIE_DOMAIN=localhost
export SERVER_AUTH_COOKIE_INSECURE=t
export SERVER_GRPC_BIND_ADDRESS=0.0.0.0
export SERVER_GRPC_INSECURE=t
export SERVER_GRPC_BROADCAST_ADDRESS=127.0.0.1:7077
export SERVER_GRPC_PORT=7077
export SERVER_URL=http://localhost:8888
export SERVER_AUTH_SET_EMAIL_VERIFIED=t
export SERVER_DEFAULT_ENGINE_VERSION=V1

cd /opt/hatchet
./hatchet-migrate
./hatchet-admin quickstart --skip certs --generated-config-dir ./config --overwrite=false
./hatchet-lite --config ./config
EOF

RUN chmod +x /usr/local/bin/start-hatchet.sh

LABEL Author="any-task-builder"
LABEL Description="Hatchet environment with local engine and Python SDK installed."

RUN mkdir -p /home/user/app

# Container contents:
#   - python3, pip, pytest, curl, git
#   - postgresql installed
#   - /usr/local/bin/start-hatchet.sh to run Hatchet local engine
#   - hatchet-sdk python package
#   - /home/user/app directory for the task

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
