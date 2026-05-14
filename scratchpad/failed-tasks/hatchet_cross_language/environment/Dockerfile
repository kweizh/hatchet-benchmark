FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    curl -fsSL https://install.hatchet.run/install.sh | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user/project && chmod 0755 /home/user /home/user/project

LABEL Author="any-task-builder"
LABEL Description="Environment for building a cross-language Hatchet workflow with Python and TypeScript."

# Container contents:
#   - Python 3 and pip installed
#   - Node.js v24 and npm installed
#   - Hatchet CLI installed
#   - /home/user/project — empty base directory for the project

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
