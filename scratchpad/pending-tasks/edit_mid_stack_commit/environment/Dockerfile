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
LABEL Description="jj (Jujutsu) colocated repo at /home/user/myrepo containing a 4-commit linear stack A->B->C->D with an empty working-copy commit @ on top of D."

# Configure a global jj user identity so any jj command run inside
# /home/user/myrepo inherits a valid author/committer identity.
RUN mkdir -p /root/.config/jj && \
    cat >/root/.config/jj/config.toml <<'EOF'
[user]
name = "Harbor User"
email = "harbor@example.com"
EOF

# Build the initial 4-commit stack:
#   - Commit A introduces a.txt
#   - Commit B introduces b.txt
#   - Commit C introduces c.txt
#   - Commit D introduces d.txt
#   - @ is an empty working-copy commit on top of D
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    jj describe -m "Commit A" && \
    echo "content for a" > a.txt && \
    jj new -m "Commit B" && \
    echo "content for b" > b.txt && \
    jj new -m "Commit C" && \
    echo "content for c" > c.txt && \
    jj new -m "Commit D" && \
    echo "content for d" > d.txt && \
    jj new && \
    jj log

# Container contents:
#   - jj v0.38.0 installed at /usr/local/bin/jj
#   - Global jj user identity configured at /root/.config/jj/config.toml
#   - /home/user/myrepo: colocated jj repo (.jj + .git) holding the stack
#       Commit A (a.txt) -> Commit B (b.txt) -> Commit C (c.txt)
#         -> Commit D (d.txt) -> @ (empty)

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
