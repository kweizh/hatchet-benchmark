FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz \
        | tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="jj (Jujutsu) v0.38.0 with a pre-initialized colocated repo at /home/user/myrepo and no user identity configured."

# Initialize a pre-existing colocated jj repo at /home/user/myrepo with NO
# user.name or user.email configured at any scope. The user must set them
# via `jj config set --user`.
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate

# Container contents:
#   - jj (Jujutsu) v0.38.0 installed at /usr/local/bin/jj
#   - /home/user/myrepo: a colocated jj/Git repository
#   - user.name and user.email are NOT configured at any scope

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
