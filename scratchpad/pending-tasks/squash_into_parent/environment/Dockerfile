FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install jj v0.38.0 (Jujutsu) from the official GitHub release
RUN curl -fsSL https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz \
        | tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj && \
    /usr/local/bin/jj --version

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Colocated jj repo at /home/user/myrepo with a parent commit 'Initial implementation' (app.py) and an empty-described working copy that modifies app.py."

# Configure a default jj user identity (used during build and at runtime).
RUN mkdir -p /root/.config/jj && \
    printf '%s\n' \
        '[user]' \
        'name = "Test User"' \
        'email = "test@example.com"' \
        > /root/.config/jj/config.toml

# Build the initial repository state:
#   1. parent commit @- : description "Initial implementation", creates app.py with "def main(): pass"
#   2. working copy @  : empty description, modifies app.py to "def main(): return 0"
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    printf 'def main(): pass\n' > app.py && \
    jj describe -m "Initial implementation" && \
    jj new && \
    printf 'def main(): return 0\n' > app.py && \
    jj status && \
    jj log

# Container contents:
#   - jj v0.38.0 installed at /usr/local/bin/jj
#   - /root/.config/jj/config.toml with user.name and user.email set
#   - /home/user/myrepo : colocated jj/git repo
#       * parent commit @- : description "Initial implementation", creates app.py = "def main(): pass"
#       * working copy @  : empty description, app.py modified to "def main(): return 0"

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
