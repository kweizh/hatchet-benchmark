# Edit a Mid-Stack Commit and Let `jj` Auto-Rebase Descendants

## Background
Jujutsu (`jj`) is a Git-compatible version control system that makes editing any commit in a stack trivial: `jj edit <change_id>` switches the working copy `@` to that commit, any file changes are auto-snapshotted into it, and all descendant commits are automatically rebased to preserve the stack. There is no need to run `git rebase -i`, mark commits as `edit`, and finish with `git rebase --continue`.

You have a pre-initialized colocated jj repository at `/home/user/myrepo`. The user identity (`user.name` and `user.email`) is already configured. The repository already contains a 4-commit linear stack:

```
@  (empty working copy on top of D)
○  Commit D   (adds d.txt)
○  Commit C   (adds c.txt)
○  Commit B   (adds b.txt)
○  Commit A   (adds a.txt)
◆  root
```

Each commit `X` introduces a single file `x.txt`.

## Requirements
1. Use `jj edit` to make the **mid-stack** `Commit B` the current working-copy commit.
2. While `@` is pointing at `Commit B`, create a new file `b_extra.txt` in the repository root containing exactly the text `extra line for B` (followed by a single trailing newline).
3. Return the working copy to the tip of the stack so that `@` is at (or above) the rebased `Commit D`. You may use either `jj edit <change_id_of_D>` or `jj new <change_id_of_D>`. Do **not** abandon, squash, or rewrite Commits C or D.
4. After you finish, the repository must look like this (the change IDs of B, C, D are stable across the rewrite, but their commit IDs will change):

   - `Commit B` contains both `b.txt` and `b_extra.txt`.
   - `Commit C` (with `c.txt`) and `Commit D` (with `d.txt`) are rebased on top of the new `Commit B` automatically.
   - The working-copy tip contains `a.txt`, `b.txt`, `b_extra.txt`, `c.txt`, and `d.txt`.

## Implementation Guide
From inside `/home/user/myrepo`:

1. List the commits to discover the change IDs:
   ```bash
   cd /home/user/myrepo
   jj log
   ```
   Note the change ID (the first short alphabetic identifier on each line) for `Commit B` and `Commit D`. You can also use revsets to capture them, e.g. `description(substring:"Commit B")`.

2. Edit `Commit B`:
   ```bash
   jj edit <change_id_of_B>
   # or:  jj edit "description(substring:\"Commit B\")"
   ```

3. Create the new file:
   ```bash
   printf 'extra line for B\n' > b_extra.txt
   ```
   The next `jj` command will auto-snapshot the file into `Commit B`. Descendants `Commit C` and `Commit D` will be auto-rebased.

4. Return to the tip:
   ```bash
   jj edit <change_id_of_D>
   # or:  jj new <change_id_of_D>
   ```

## Constraints
- Project path: /home/user/myrepo
- Use `jj` commands only — do NOT use `git` directly.
- Do NOT modify the descriptions of any commit (they must remain exactly `Commit A`, `Commit B`, `Commit C`, `Commit D`).
- Do NOT delete, abandon, squash, or fold any of the four commits.
- The new file must be named exactly `b_extra.txt` and contain exactly `extra line for B` (plus one trailing newline).
- After completion, `b.txt`, `b_extra.txt`, `c.txt`, and `d.txt` must all be visible in the working-copy tip.
