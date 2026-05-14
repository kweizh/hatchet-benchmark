# Move a Bookmark Forward in Jujutsu

## Background
Jujutsu (`jj`) is a modern, Git-compatible version control system. Unlike Git branches, `jj` uses **bookmarks** — named pointers to specific commits that do *not* automatically follow new commits. To advance a bookmark, you must explicitly move it using `jj bookmark move` (or equivalently `jj bookmark set` for an existing bookmark).

A Jujutsu repository is already initialized at `/home/user/myrepo`. The repo is colocated with Git (it has both a `.jj/` and a `.git/` directory) and user identity has been pre-configured. The repository has a strict linear history of exactly three user-created commits (oldest → newest):

1. A commit with description `Commit 1`.
2. A commit with description `Commit 2`.
3. A commit with description `Commit 3`.

On top of `Commit 3` there is an empty working-copy commit (`@`), which has no description and no file changes. A local bookmark named `feature` already exists and points to the commit whose description is `Commit 2`.

## Requirements
- Move the existing local bookmark `feature` forward so that it points to the commit whose description is `Commit 3`.
- The move must be a *fast-forward* move — that is, it must advance the bookmark to a descendant of its current position (no `--allow-backwards` flag is needed).
- After the operation:
  - The bookmark `feature` must still exist as a local bookmark.
  - The commit at which the bookmark `feature` resolves must have description `Commit 3` (and not `Commit 2`).
  - The commit with description `Commit 1`, `Commit 2`, and `Commit 3` must all still exist with the same descriptions. Do not rewrite any commit.

## Implementation Guide
1. `cd /home/user/myrepo`
2. Inspect the current state of the bookmark if you wish:
   ```bash
   jj bookmark list feature
   jj log -r 'feature' --no-graph -T 'description.first_line()'
   ```
3. Find the change ID of the commit with description `Commit 3` (it is the parent of the working copy):
   ```bash
   jj log -r 'description(substring:"Commit 3")' --no-graph -T 'change_id ++ "\n"'
   ```
4. Move the `feature` bookmark to that commit using either form:
   - `jj bookmark move feature --to 'description(substring:"Commit 3")'`
   - or `jj bookmark set feature -r 'description(substring:"Commit 3")'`
5. Confirm with `jj log -r 'feature' --no-graph -T 'description.first_line()'`. The output must be exactly `Commit 3`.

## Constraints
- Project path: /home/user/myrepo
- Use the real `jj` binary that is pre-installed in the environment. Do not mock or stub `jj`.
- Do not modify or rewrite any existing commit (no `jj describe`, no `jj edit`, no `jj rebase` of `Commit 1` / `Commit 2` / `Commit 3`).
- Do not delete or recreate the `feature` bookmark (no `jj bookmark delete feature` followed by `jj bookmark create`).
