FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL \
        https://github.com/jj-vcs/jj/releases/download/v0.38.0/jj-v0.38.0-x86_64-unknown-linux-musl.tar.gz | \
        tar -xz -C /usr/local/bin ./jj && \
    chmod +x /usr/local/bin/jj

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="jj 0.38.0 colocated repo at /home/user/myrepo with a 3-commit linear stack (Setup, Implementation, Tests) and an empty working-copy child."

# Pre-configure global jj identity and bootstrap the colocated repo with a
# linear 3-commit stack: Setup (setup.py) -> Implementation (main.py) -> Tests (test_main.py).
# The working copy is left as an empty child of the Tests commit.
RUN jj config set --user user.name "Harbor Tester" && \
    jj config set --user user.email "harbor-tester@example.com" && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    echo '# setup' > setup.py && \
    jj describe -m "Setup" && \
    jj new -m "Implementation" && \
    echo '# main' > main.py && \
    jj new -m "Tests" && \
    echo '# tests' > test_main.py && \
    jj new && \
    jj status

# Container contents:
#   - jj v0.38.0 binary installed at /usr/local/bin/jj
#   - Global jj user identity configured (Harbor Tester / harbor-tester@example.com)
#   - /home/user/myrepo: colocated jj/Git repo
#       * change "Setup" creates setup.py = "# setup"
#       * change "Implementation" creates main.py = "# main"
#       * change "Tests" creates test_main.py = "# tests"
#       * @ is an empty child of "Tests"

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
