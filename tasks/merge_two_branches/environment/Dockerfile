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
LABEL Description="Colocated jj+git repository at /home/user/myrepo with two diverged bookmarks (branch_x, branch_y) sharing a common Base ancestor, ready for a merge commit task."

# Configure global jj identity and build the initial diverged history:
#   Base commit (shared.txt)
#     |-> Branch X commit (x.txt)        <-- bookmark: branch_x
#     |-> Branch Y commit (y.txt)        <-- bookmark: branch_y
#   Working copy @ is a new empty commit on top of the branch_x tip.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'shared content' > shared.txt && \
    jj describe -m "Base commit" && \
    jj new -m "Branch X commit" && \
    printf 'x' > x.txt && \
    jj new && \
    jj bookmark create branch_x -r '@-' && \
    jj new 'description(substring:"Base commit")' -m "Branch Y commit" && \
    printf 'y' > y.txt && \
    jj new && \
    jj bookmark create branch_y -r '@-' && \
    jj edit 'branch_x' && \
    jj new && \
    jj log -r 'all()' --no-graph -T 'description.first_line() ++ "\n"'

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository with two diverged branches
#       - Base commit  -> adds shared.txt = "shared content"
#       - branch_x bookmark -> Branch X commit (adds x.txt = "x")
#       - branch_y bookmark -> Branch Y commit (adds y.txt = "y")
#       - working copy @ is a new empty commit on top of branch_x

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
