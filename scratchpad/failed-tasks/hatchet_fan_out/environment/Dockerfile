FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk pydantic

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Hatchet durable task fan-out environment with a sample input.csv."

RUN mkdir -p /home/user/hatchet_project && \
    cd /home/user/hatchet_project && \
    cat >input.csv <<'EOF'
id,name
1,Alice
2,Bob
3,Charlie
EOF

# Container contents:
#   - hatchet-sdk installed.
#   - /home/user/hatchet_project  — project directory
#   - /home/user/hatchet_project/input.csv — sample input data

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
