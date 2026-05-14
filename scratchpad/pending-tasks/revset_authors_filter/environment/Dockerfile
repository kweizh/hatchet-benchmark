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
LABEL Description="Colocated jj+git repo at /home/user/myrepo containing 5 commits authored by Alice, Bob, and Charlie with mixed 'fix' and 'add' descriptions."

# Configure a global jj identity so jj can run commands.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml

# Initialize the colocated repo and create the 5 user commits with the
# specified authors and descriptions. Each `jj describe --author` rewrites
# the current working-copy commit to set its description and author, then
# `jj new` starts a fresh empty child commit for the next iteration.
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'content of file1\n' > file1.txt && \
    jj describe -m "fix login bug" --author "Alice <alice@example.com>" && \
    jj new && \
    printf 'content of file2\n' > file2.txt && \
    jj describe -m "fix database" --author "Bob <bob@example.com>" && \
    jj new && \
    printf 'content of file3\n' > file3.txt && \
    jj describe -m "add feature X" --author "Alice <alice@example.com>" && \
    jj new && \
    printf 'content of file4\n' > file4.txt && \
    jj describe -m "fix typo in README" --author "Alice <alice@example.com>" && \
    jj new && \
    printf 'content of file5\n' > file5.txt && \
    jj describe -m "add tests" --author "Charlie <charlie@example.com>" && \
    jj new && \
    jj log -r 'author(substring:"Alice") & description(substring:"fix")' --no-graph -T 'change_id ++ "\n"'

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository with five user commits:
#       1. Alice <alice@example.com>   "fix login bug"      (file1.txt)
#       2. Bob   <bob@example.com>     "fix database"       (file2.txt)
#       3. Alice <alice@example.com>   "add feature X"      (file3.txt)
#       4. Alice <alice@example.com>   "fix typo in README" (file4.txt)
#       5. Charlie <charlie@example.com> "add tests"        (file5.txt)
#     Plus an empty working-copy commit on top of commit 5.

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
