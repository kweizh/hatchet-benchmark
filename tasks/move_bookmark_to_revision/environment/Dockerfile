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
LABEL Description="Colocated jj+git repository at /home/user/myrepo with a linear history of three commits (Commit 1, Commit 2, Commit 3), an empty working-copy child of Commit 3, and a local bookmark 'feature' pointing to Commit 2."

# Configure global jj identity and create the initial repository state with three
# linear commits and a 'feature' bookmark pointing to the middle commit.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'content 1\n' > file1.txt && \
    jj describe -m "Commit 1" && \
    jj new -m "Commit 2" && \
    printf 'content 2\n' > file2.txt && \
    jj new -m "Commit 3" && \
    printf 'content 3\n' > file3.txt && \
    jj new && \
    jj bookmark create feature -r 'description(substring:"Commit 2")' && \
    jj log --no-graph -T 'change_id ++ " " ++ description.first_line() ++ "\n"'

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository with linear history:
#       - Commit 1 (oldest) introduces file1.txt
#       - Commit 2 (middle) introduces file2.txt
#       - Commit 3 (newest non-empty) introduces file3.txt
#       - working copy @ is an empty commit on top of Commit 3
#       - local bookmark 'feature' points to the commit with description 'Commit 2'

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
