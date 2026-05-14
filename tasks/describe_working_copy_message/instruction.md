# Describe the Working Copy Commit and Start a New Change

## Background
Jujutsu (`jj`) is a Git-compatible version control system that treats the working copy as a permanent commit (referenced by `@`). When you make file changes, they are automatically recorded into the working-copy commit. Initially, this commit has an empty description. You can give the commit a meaningful description with `jj describe -m "<message>"` and then start a fresh, empty change for the next batch of work with `jj new`.

You have a pre-initialized colocated jj repository at `/home/user/myrepo`. The user identity (`user.name` and `user.email`) is already configured. The working-copy commit `@` currently has an empty description and contains uncommitted changes to a file named `README.md`.

## Requirements
1. Set the description of the current working-copy commit to exactly `Add README documentation`.
2. After describing it, create a new empty change on top of that commit so that the new working-copy commit `@` is empty and the described commit becomes its parent (`@-`).

## Implementation Guide
From inside `/home/user/myrepo`, run:

```bash
cd /home/user/myrepo
jj describe -m "Add README documentation"
jj new
```

The `-m` flag passes the message non-interactively (no editor is opened). `jj new` (with no arguments) creates a new empty change whose parent is the current working-copy commit, and switches `@` to point to that new empty change.

## Constraints
- Project path: /home/user/myrepo
- Do NOT use `git` directly for this task; use `jj` commands only.
- The description must match exactly: `Add README documentation` (case-sensitive, no trailing punctuation, no quotes).
- After completing the task, the new working-copy commit `@` must be empty (no file changes).
- The previous commit (now `@-`) must contain the changes to `README.md` and the description `Add README documentation`.
