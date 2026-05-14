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
LABEL Description="Colocated jj+git repository at /home/user/myrepo with a linear chain Commit A -> Commit B -> Commit C and an empty working-copy on top."

# Configure global jj identity and create the initial repository state.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'content A' > a.txt && \
    jj describe -m "Commit A" && \
    jj new -m "Commit B" && \
    printf 'content B' > b.txt && \
    jj new -m "Commit C" && \
    printf 'content C' > c.txt && \
    jj new && \
    jj log

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository
#       - Linear chain: "Commit A" (a.txt) -> "Commit B" (b.txt) -> "Commit C" (c.txt)
#       - Each commit description: "Commit A", "Commit B", "Commit C"
#       - File contents: a.txt="content A", b.txt="content B", c.txt="content C"
#       - Working copy @ is a new empty commit on top of "Commit C"

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
