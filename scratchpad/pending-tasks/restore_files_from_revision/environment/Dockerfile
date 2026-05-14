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
LABEL Description="Colocated jj repo at /home/user/myrepo with two non-root commits ('Initial config' creating config.json={version:1.0}, 'Update config and add extras' modifying config.json to {version:2.0} and adding extra.txt) plus an empty working copy @ on top."

# Configure a default jj user identity (used during build and at runtime).
RUN mkdir -p /root/.config/jj && \
    printf '%s\n' \
        '[user]' \
        'name = "Test User"' \
        'email = "test@example.com"' \
        > /root/.config/jj/config.toml

# Build the initial repository state:
#   1. commit @--: description "Initial config", creates config.json = {"version": "1.0"}
#   2. commit @- : description "Update config and add extras", modifies config.json
#                  to {"version": "2.0"} and adds extra.txt = "additional data"
#   3. commit @  : empty working copy on top of @-
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    printf '{"version": "1.0"}\n' > config.json && \
    jj describe -m "Initial config" && \
    jj new -m "Update config and add extras" && \
    printf '{"version": "2.0"}\n' > config.json && \
    printf 'additional data\n' > extra.txt && \
    jj new && \
    jj status && \
    jj log

# Container contents:
#   - jj v0.38.0 installed at /usr/local/bin/jj
#   - /root/.config/jj/config.toml with user.name and user.email set
#   - /home/user/myrepo: colocated jj/git repo with three non-root commits:
#       * @-- "Initial config"               : creates config.json = {"version": "1.0"}
#       * @-  "Update config and add extras" : config.json -> {"version": "2.0"}, adds extra.txt
#       * @   (empty, no description)        : working copy on top of @-

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
