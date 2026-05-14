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
LABEL Description="Colocated jj+git repository at /home/user/myrepo seeded with three commits (Initial commit, Add feature B, Fix bug C) plus an empty working-copy commit on top, used for exercising custom jj log templates."

# Configure a global jj identity and seed the repository with three commits, each
# adding a different file, and leave an empty working-copy commit on top.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    printf 'content of file 1\n' > file1.txt && \
    jj describe -m "Initial commit" && \
    jj new && \
    printf 'content of file 2\n' > file2.txt && \
    jj describe -m "Add feature B" && \
    jj new && \
    printf 'content of file 3\n' > file3.txt && \
    jj describe -m "Fix bug C" && \
    jj new && \
    jj log --no-graph -r 'all() ~ root()' -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'

# Container contents:
#   - Ubuntu 24.04 with curl, ca-certificates, git, python3, python3-pytest, bash
#   - jj v0.38.0 binary installed at /usr/local/bin/jj
#   - /root/.config/jj/config.toml — global jj user identity ("Harbor Tester")
#   - /home/user/myrepo — colocated jj+git repository with:
#       * commit "Initial commit" adding file1.txt
#       * commit "Add feature B" adding file2.txt
#       * commit "Fix bug C" adding file3.txt
#       * empty working-copy commit @ on top
#   - no log_output.txt yet — the agent must produce it via `jj log`

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
