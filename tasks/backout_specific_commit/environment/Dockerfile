FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install jj v0.38.0 (Jujutsu) from the official GitHub release
RUN curl -fsSL https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz \
        | tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj && \
    /usr/local/bin/jj --version

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Colocated jj repo at /home/user/myrepo with a 3-commit linear history (Initial app, Bad change, Add documentation) and an empty working copy on top."

# Configure a default jj user identity (used during build and at runtime).
RUN mkdir -p /root/.config/jj && \
    printf '%s\n' \
        '[user]' \
        'name = "Test User"' \
        'email = "test@example.com"' \
        > /root/.config/jj/config.toml

# Build the initial repository state:
#   A) Initial app       : creates app.py = 'print("hello")\n'
#   B) Bad change        : modifies app.py to add 'print("BUG: do not commit")\n'
#   C) Add documentation : creates README.md = 'Project docs\n'
#   D) @ working copy    : empty commit on top of "Add documentation"
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    printf 'print("hello")\n' > app.py && \
    jj describe -m "Initial app" && \
    jj new -m "Bad change" && \
    printf 'print("hello")\nprint("BUG: do not commit")\n' > app.py && \
    jj new -m "Add documentation" && \
    printf 'Project docs\n' > README.md && \
    jj new && \
    jj log

# Container contents:
#   - jj v0.38.0 installed at /usr/local/bin/jj
#   - /root/.config/jj/config.toml with user.name and user.email set
#   - /home/user/myrepo : colocated jj/git repo with 3 named commits + an empty working copy on top
#       * Initial app       : app.py = print("hello")
#       * Bad change        : app.py adds print("BUG: do not commit")
#       * Add documentation : README.md = "Project docs"
#       * @ (working copy)  : empty

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
