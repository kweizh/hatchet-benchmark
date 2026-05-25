###############################################################################
# Stage 1: pull binaries from the official hatchet-lite image
###############################################################################
FROM ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest AS hatchet-bin

###############################################################################
# Stage 2: ubuntu-based runtime that bundles postgres + hatchet-lite + python
#          + a tiny mock LLM HTTP server (Flask).
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
        python-dotenv \
        requests \
        flask && \
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
# can be embedded into the image.
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

###############################################################################
# Mock LLM HTTP server.
#
# A tiny Flask app that exposes:
#   - GET  /health -> 200 OK
#   - POST /reset  -> resets the per-process call counter to 0
#   - POST /chat   -> reads {"messages": [...]} and responds with
#                     {"reply": "<turn>: " + last_user_message}, appending
#                     " [DONE]" on the 3rd call.
#
# The counter is persisted in /var/lib/mock-llm/counter.json so that the
# `[DONE]` signal is deterministic across the agent loop and replays of the
# Hatchet durable task.
###############################################################################
RUN mkdir -p /opt/mock-llm /var/lib/mock-llm && \
    chmod 0777 /var/lib/mock-llm
RUN printf '%s\n' \
    'import json' \
    'import os' \
    'from flask import Flask, jsonify, request' \
    '' \
    'COUNTER_PATH = "/var/lib/mock-llm/counter.json"' \
    'DONE_AT = int(os.environ.get("MOCK_LLM_DONE_AT", "3"))' \
    '' \
    'app = Flask(__name__)' \
    '' \
    'def _read():' \
    '    try:' \
    '        with open(COUNTER_PATH, "r") as f:' \
    '            return int(json.load(f).get("count", 0))' \
    '    except Exception:' \
    '        return 0' \
    '' \
    'def _write(n):' \
    '    with open(COUNTER_PATH, "w") as f:' \
    '        json.dump({"count": int(n)}, f)' \
    '' \
    '@app.get("/health")' \
    'def health():' \
    '    return jsonify({"status": "ok", "count": _read(), "done_at": DONE_AT})' \
    '' \
    '@app.post("/reset")' \
    'def reset():' \
    '    _write(0)' \
    '    return jsonify({"ok": True, "count": 0})' \
    '' \
    '@app.post("/chat")' \
    'def chat():' \
    '    body = request.get_json(silent=True) or {}' \
    '    messages = body.get("messages", []) or []' \
    '    last_user = ""' \
    '    for m in reversed(messages):' \
    '        if isinstance(m, dict) and m.get("role") == "user":' \
    '            last_user = str(m.get("content", ""))' \
    '            break' \
    '    n = _read() + 1' \
    '    _write(n)' \
    '    reply = "{}: {}".format(n, last_user)' \
    '    if n >= DONE_AT:' \
    '        reply = reply + " [DONE]"' \
    '    return jsonify({"reply": reply, "turn": n})' \
    '' \
    'if __name__ == "__main__":' \
    '    _write(0)' \
    '    app.run(host="0.0.0.0", port=9100, threaded=True)' \
    > /opt/mock-llm/server.py && \
    chmod 0644 /opt/mock-llm/server.py

# Runtime entrypoint: start postgres + hatchet-lite + mock LLM, then keep alive.
RUN printf '%s\n' \
    '#!/bin/bash' \
    'set -e' \
    '' \
    'mkdir -p /var/run/postgresql /var/log/postgresql /var/lib/mock-llm' \
    'chown postgres:postgres /var/run/postgresql /var/log/postgresql' \
    'chmod 0777 /var/lib/mock-llm' \
    '' \
    '# Reset the mock LLM counter on container start so deterministic [DONE].' \
    'echo "{\"count\": 0}" > /var/lib/mock-llm/counter.json' \
    '' \
    '# Start postgres' \
    'pg_ctlcluster ${PG_VERSION} main start' \
    '' \
    '# Start hatchet-lite in background' \
    'nohup hatchet-lite --config /hatchet-config >/var/log/hatchet-lite.log 2>&1 &' \
    '' \
    '# Start the mock LLM HTTP server in background' \
    'nohup python3 /opt/mock-llm/server.py >/var/log/mock-llm.log 2>&1 &' \
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
    '# Wait until the mock LLM is accepting HTTP connections.' \
    'for i in $(seq 1 30); do' \
    '  if (echo > /dev/tcp/127.0.0.1/9100) 2>/dev/null; then' \
    '    echo "mock-llm ready on :9100"' \
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
LABEL Description="Hatchet durable AI agent loop (Python) task environment: ubuntu:24.04 with PostgreSQL 16, a self-hosted hatchet-lite engine, hatchet-sdk + requests + flask for Python, a pre-bootstrapped HATCHET_CLIENT_TOKEN, and a bundled deterministic mock LLM HTTP server on :9100 that emits [DONE] on its 3rd reply."

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
#   - /opt/mock-llm/server.py: tiny Flask mock LLM exposed on :9100 with /chat, /reset, /health
#   - /var/lib/mock-llm/counter.json: deterministic per-process call counter for the mock LLM
#   - /usr/local/bin/zealt-startup.sh: starts postgres + hatchet-lite + mock LLM at container boot
#   - hatchet-sdk + pytest-xprocess + python-dotenv + requests + flask installed
#   - /home/user/myproject: empty project directory where the agent builds the durable task
