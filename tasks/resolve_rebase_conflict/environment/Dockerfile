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
LABEL Description="Colocated jj+git repository at /home/user/myrepo with a CONFLICT in config.yaml produced by a rebase of branch-b onto branch-a."

# Build the initial conflicted state:
#   Base                   (bookmark: base)   config.yaml: timeout: 30
#     |
#     Increase timeout to 60   (bookmark: branch-a)   config.yaml: timeout: 60
#     |
#     Increase timeout to 120  (bookmark: branch-b)   <-- @ here, CONFLICTED
#
# Construction:
#  - Create Base with `timeout: 30` in config.yaml.
#  - Create child of Base, set to `timeout: 60`, place branch-a there.
#  - Create another child of Base, set to `timeout: 120`, place branch-b there.
#  - `jj rebase -s branch-b -d branch-a` moves branch-b on top of branch-a; the
#    change `30 -> 120` cannot apply on top of `60`, so the rebased branch-b
#    commit carries a conflict in config.yaml.
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'timeout: 30\n' > config.yaml && \
    jj describe -m "Base" && \
    jj bookmark create base -r @ && \
    jj new -m "Increase timeout to 60" && \
    printf 'timeout: 60\n' > config.yaml && \
    jj bookmark create branch-a -r @ && \
    jj new -m "Increase timeout to 120" 'description(substring:"Base")' && \
    printf 'timeout: 120\n' > config.yaml && \
    jj bookmark create branch-b -r @ && \
    jj rebase -s branch-b -d branch-a && \
    jj status && \
    jj log -r 'conflicts()' --no-graph -T 'change_id ++ "\n"'

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for running tests
#   - /root/.config/jj/config.toml: user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository in a conflicted state
#       - bookmark `base` -> commit "Base" (config.yaml: timeout: 30)
#       - bookmark `branch-a` -> commit "Increase timeout to 60"
#       - bookmark `branch-b` -> rebased commit "Increase timeout to 120" (conflicted)
#       - working copy @ is on the conflicted branch-b commit
#       - config.yaml in the working copy contains jj conflict markers

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
