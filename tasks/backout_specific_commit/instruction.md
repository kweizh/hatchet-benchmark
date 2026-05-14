# Revert a Specific Buggy Commit in a jj History

## Background
You have a colocated Jujutsu (`jj`) repository at `/home/user/myrepo`. The repository contains three non-root commits in a linear stack (oldest to newest):

1. `Initial app` — creates `app.py` with the body:

   ```python
   print("hello")
   ```

2. `Bad change` — modifies `app.py` to:

   ```python
   print("hello")
   print("BUG: do not commit")
   ```

3. `Add documentation` — creates `README.md` with the body `Project docs`.

The working copy `@` is a new empty commit on top of `Add documentation`. The `jj` binary is installed at `/usr/local/bin/jj` and the user identity is pre-configured.

Note: As of jj 0.38, the `jj backout` command has been removed and replaced by `jj revert`, which provides the same functionality with cleaner flags.

## Requirements
Use the `jj revert` command to create a new commit in the ancestry of the working copy `@` that applies the reverse of the `Bad change` commit, so that the buggy line is undone in the working copy. After the operation:

- The buggy line `print("BUG: do not commit")` MUST be removed from `app.py` on disk.
- `app.py` MUST contain exactly `print("hello")` (a single line, plus a trailing newline).
- `README.md` MUST still exist with the content `Project docs`.
- The original three commits (`Initial app`, `Bad change`, `Add documentation`) MUST still be present in the repo history.
- A new commit MUST exist in the ancestry of `@` that contains the inverse of `Bad change`.

## Implementation Guide
1. `cd /home/user/myrepo`.
2. Identify the `Bad change` commit using a revset such as `description(substring:"Bad change")`.
3. Run `jj revert -r 'description(substring:"Bad change")' --insert-before @` to insert the reverse of that commit into the graph just before the working copy. `jj` will automatically rebase the working copy so that `@` becomes a child of the revert commit, and the files on disk will reflect the reverted state.
   (Equivalent short flag: `-B @`. If you instead use `--destination @` / `--onto @` / `-A @`, the revert commit will be created as a child of `@` and you will additionally need to move the working copy onto it, e.g. with `jj new <revert-change-id>` or `jj edit <revert-change-id>`, so that the working files show the reverted state.)
4. Verify with `jj log` that all three original commits are still listed and that a new commit titled `Revert "Bad change"` has been added to the ancestry of `@`.
5. Verify with `cat app.py` that the buggy line is gone and the file is back to `print("hello")`.
6. Verify with `cat README.md` that documentation is preserved.

## Constraints
- Project path: /home/user/myrepo
- Do NOT manually edit `.jj/` or `.git/` internals; only use the `jj` CLI.
- Do NOT use `jj abandon` to remove the `Bad change` commit — the history of all three original commits must be preserved.
- Do NOT directly rewrite `app.py` to remove the buggy line; use the `jj revert` flow.
- The final content of `app.py` must be exactly `print("hello")\n` (no trailing buggy line).
- The final content of `README.md` must be exactly `Project docs\n`.
