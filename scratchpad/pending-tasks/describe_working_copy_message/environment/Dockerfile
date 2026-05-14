FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz | tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="jj (Jujutsu) colocated repo at /home/user/myrepo with an empty-description working-copy commit containing uncommitted README.md changes."

# Configure a global jj user identity (so any jj command in /home/user/myrepo
# inherits a valid author/committer) and pre-create the colocated repo with
# uncommitted changes to README.md.
RUN mkdir -p /root/.config/jj && \
    cat >/root/.config/jj/config.toml <<'EOF'
[user]
name = "Harbor User"
email = "harbor@example.com"
EOF

RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    printf '%s\n' '# My Project' '' 'Initial README content for the harbor task.' > README.md && \
    # Trigger a snapshot so the working-copy commit @ records the README.md
    # change while keeping the description empty.
    jj status

# Container contents:
#   - jj v0.38.0 installed at /usr/local/bin/jj
#   - Global jj user identity configured in /root/.config/jj/config.toml
#   - /home/user/myrepo: colocated jj repo (.jj and .git) with README.md
#     present as uncommitted change recorded into the working-copy commit @,
#     which has an empty description.

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
