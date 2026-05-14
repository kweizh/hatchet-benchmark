# Create a Bookmark and Push It to a Local Git Remote

## Background
Jujutsu (`jj`) is a modern, Git-compatible version control system. Unlike Git branches, `jj` allows commits to be *anonymous* (not pointed to by any named bookmark). To share a commit with a Git remote (e.g., the `origin` remote), you must first create a **bookmark** that points to the commit, and then push that bookmark with `jj git push`.

A colocated jj+git repository is already initialized at `/home/user/myrepo` (it has both a `.jj/` directory and a `.git/` directory). The user identity is pre-configured globally. The repository has a strictly linear history of two user-created commits (oldest → newest):

1. A commit with description `First` that introduces the file `first.txt`.
2. A commit with description `Second` that introduces the file `second.txt`.

On top of `Second` there is an empty anonymous working-copy commit (`@`) — it has no description and no file changes. There are currently **no local or remote bookmarks** in the repository.

There is also a **local bare Git repository** at `/home/user/remote.git` that has been configured as the `origin` Git remote of `/home/user/myrepo`. This bare repo is currently empty (no refs). All communication with the remote happens via the local filesystem — no network access is needed.

## Requirements
- Create a new **local** bookmark named `my-feature` that points to the parent of the working copy (`@-`) — i.e., the commit with description `Second`.
- Push that bookmark to the `origin` remote so that the bare Git repository at `/home/user/remote.git` has a ref `refs/heads/my-feature` pointing to the same commit (by Git commit ID) as the local bookmark.
- The original commits `First` and `Second` must still exist with the same descriptions and the same Git commit IDs. Do not rewrite, abandon, rebase, squash, or otherwise modify any existing commit.
- Do not create any other local bookmark. Only `my-feature` may be created.

## Implementation Guide
1. `cd /home/user/myrepo`
2. Inspect the current state if you wish:
   ```bash
   jj log
   jj bookmark list
   jj git remote list
   ```
3. Create the local bookmark `my-feature` pointing to `@-` (the `Second` commit):
   ```bash
   jj bookmark create my-feature -r @-
   ```
4. Push the bookmark to the `origin` remote:
   ```bash
   jj git push --bookmark my-feature
   ```
   (`-b my-feature` is an accepted short form.)
5. Verify the push succeeded:
   ```bash
   jj bookmark list my-feature
   git --git-dir=/home/user/remote.git show-ref refs/heads/my-feature
   ```

## Constraints
- Project path: `/home/user/myrepo`
- Remote bare repository path: `/home/user/remote.git`
- Remote name: `origin`
- Bookmark name to create and push: `my-feature`
- Use the real `jj` binary that is pre-installed in the environment. Do not mock or stub `jj` or `git`.
- Do not change the URL of the `origin` remote and do not add any other remote.
- Do not push using raw `git push` against the working repo — the push must go through `jj git push` so that jj tracks the remote bookmark.
