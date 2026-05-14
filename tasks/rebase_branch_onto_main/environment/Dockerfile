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
LABEL Description="Colocated jj+git repository at /home/user/myrepo with diverged main and feature bookmarks (2 commits each) sharing a common Base ancestor."

# Configure global jj identity and build the initial diverged history:
#   root -> Base
#         -> Main1 -> Main2   (main bookmark on Main2)
#         -> Feat1 -> Feat2   (feature bookmark on Feat2, working copy @ empty on top)
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Harbor Tester"\nemail = "tester@harbor.local"\n' > /root/.config/jj/config.toml && \
    mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    git init -q -b main && \
    jj git init --colocate && \
    printf 'base content' > base.txt && \
    jj describe -m "Base" && \
    jj new -m "Main1" && \
    printf 'main1 content' > main1.txt && \
    jj new -m "Main2" && \
    printf 'main2 content' > main2.txt && \
    jj new && \
    jj bookmark create main -r '@-' && \
    jj new 'description(substring:"Base")' -m "Feat1" && \
    printf 'feat1 content' > feat1.txt && \
    jj new -m "Feat2" && \
    printf 'feat2 content' > feat2.txt && \
    jj new && \
    jj bookmark create feature -r '@-' && \
    jj log -r 'all()' --no-graph -T 'description.first_line() ++ "\n"'

# Container contents:
#   - jj v0.38.0 installed in /usr/local/bin/jj
#   - python3 + pytest available for tests
#   - /root/.config/jj/config.toml: global user.name and user.email configured
#   - /home/user/myrepo: colocated jj+git repository with two diverged branches
#       - main bookmark -> Main2 (Base -> Main1 -> Main2, adds main1.txt and main2.txt)
#       - feature bookmark -> Feat2 (Base -> Feat1 -> Feat2, adds feat1.txt and feat2.txt)
#       - working copy @ is a new empty commit on top of Feat2

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
