FROM ubuntu:24.04

RUN apt-get update -y &&     DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends         curl ca-certificates git python3 python3-pip python3-pytest bash &&     apt-get clean &&     rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages hatchet-sdk pydantic

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Hatchet Python SDK environment for cron workflow task."

RUN mkdir -p /home/user/app &&     cd /home/user/app &&     cat >records.json <<EOF
[
  {"id": 1},
  {"id": 2},
  {"id": 3}
]
EOF

# Container contents:
#   - hatchet-sdk installed
#   - /home/user/app  — project directory
#   - records.json with 3 records

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
