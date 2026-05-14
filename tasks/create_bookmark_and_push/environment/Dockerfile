FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz \
        | tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Colocated jj+git repo /home/user/myrepo with two commits (First, Second) on top of an empty working copy, and a local bare git remote /home/user/remote.git wired as origin. No bookmarks exist yet."

# Configure global jj identity, create the bare git remote, and seed the colocated
# jj/git repository with two linear commits (First, Second) and an empty working copy.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    git init --bare -b main /home/user/remote.git && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    git remote add origin /home/user/remote.git && \
    jj git init --colocate && \
    printf 'first content\n' > first.txt && \
    jj describe -m "First" && \
    jj new -m "Second" && \
    printf 'second content\n' > second.txt && \
    jj new && \
    jj git fetch --remote origin || true && \
    jj log --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/remote.git: empty bare git repository (no refs yet) — acts as 'origin'
#   - /home/user/myrepo: colocated jj+git repository with:
#       - 'origin' git remote pointing at /home/user/remote.git
#       - Commit with description "First" introducing first.txt
#       - Commit with description "Second" introducing second.txt (child of "First")
#       - Empty working-copy commit @ on top of "Second" (no description, no changes)
#       - No local or remote bookmarks

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
