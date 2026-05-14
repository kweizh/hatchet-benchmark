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
LABEL Description="jj (Jujutsu) repo at /home/user/myrepo with a 4-commit stack whose oldest commit contains a typo in greeting.txt."

# Configure jj user identity for root (which is the user inside the container).
RUN mkdir -p /root/.config/jj && \
    printf '[user]\nname = "Test User"\nemail = "test@example.com"\n' > /root/.config/jj/config.toml

# Build the initial repository state:
#   * colocated jj/git repo at /home/user/myrepo
#   * 4-commit chain (oldest -> newest): "Add greeting" (greeting.txt = "Helo World"),
#     "Add feature 1" (feature1.txt), "Add feature 2" (feature2.txt), "Add feature 3" (feature3.txt)
#   * empty working-copy commit @ on top
RUN mkdir -p /home/user/myrepo && \
    cd /home/user/myrepo && \
    jj git init --colocate && \
    printf 'Helo World\n' > greeting.txt && \
    jj describe -m "Add greeting" && \
    jj new -m "Add feature 1" && \
    printf 'feature 1\n' > feature1.txt && \
    jj new -m "Add feature 2" && \
    printf 'feature 2\n' > feature2.txt && \
    jj new -m "Add feature 3" && \
    printf 'feature 3\n' > feature3.txt && \
    jj new && \
    jj status

# Container contents:
#   - jj v0.38.0 installed at /usr/local/bin/jj
#   - /root/.config/jj/config.toml with user identity configured
#   - /home/user/myrepo: colocated jj/git repository with the 4-commit stack described above

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]
