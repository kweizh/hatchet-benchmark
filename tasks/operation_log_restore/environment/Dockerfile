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
LABEL Description="Colocated jj+git repository at /home/user/myrepo whose operation log contains an abandoned Stage 2 state that must be recovered via jj op restore."

# Configure global jj identity and create the initial repository state.
# Sequence of operations performed (recorded in op log):
#   1. jj git init --colocate
#   2. write file1.txt; jj commit -m "Stage 1"          (creates Stage 1 with file1.txt)
#   3. write file2.txt; jj commit -m "Stage 2"          (creates Stage 2 with file2.txt) <-- TARGET STATE
#   4. write file3.txt; jj commit -m "Stage 3"          (creates Stage 3 with file3.txt)
#   5. jj abandon -r description("Stage 2")             (Stage 3 rebased onto Stage 1; file2.txt gone)
#   6. jj new -m "extra1"
#   7. jj new -m "extra2"
# Final visible state: Stage 1 (file1.txt) -> Stage 3 (file3.txt) -> extra1 -> extra2 -> @
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'content A\n' > file1.txt && \
    jj commit -m "Stage 1" && \
    printf 'content B\n' > file2.txt && \
    jj commit -m "Stage 2" && \
    printf 'content C\n' > file3.txt && \
    jj commit -m "Stage 3" && \
    jj abandon -r 'description(substring:"Stage 2")' && \
    jj new -m "extra1" && \
    jj new -m "extra2" && \
    jj log && \
    jj op log

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository
#       - Visible commits: "Stage 1" (file1.txt), "Stage 3" (file3.txt), "extra1", "extra2"
#       - "Stage 2" (and file2.txt) abandoned; recoverable only via `jj op restore <op_id>`
#       - Working dir contains file1.txt and file3.txt; file2.txt absent

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
