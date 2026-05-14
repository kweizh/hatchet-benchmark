FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz | \
        tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Empty /home/user/myrepo directory plus jj v0.38.0 ready to initialize a colocated jj/Git repository."

# Pre-create the empty project directory and pre-configure a jj user identity so
# that `jj git init --colocate` does not prompt for one in a non-interactive
# evaluation environment.
RUN mkdir -p /home/user/myrepo && \
    chmod 0755 /home/user/myrepo && \
    mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor User"\nemail = "harbor@example.com"\n' > /root/.config/jj/config.toml

# Container contents:
#   - Ubuntu 24.04 base with curl, ca-certificates, git, python3, python3-pytest, bash
#   - jj v0.38.0 binary installed at /usr/local/bin/jj
#   - /home/user — base user home directory
#   - /home/user/myrepo — empty directory ready for `jj git init --colocate`
#   - /root/.config/jj/config.toml — pre-configured jj user identity so init does not prompt

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
