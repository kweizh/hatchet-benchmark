# Merge Two Diverged Branches in Jujutsu

## Background
Jujutsu (`jj`) is a modern, Git-compatible version control system. Unlike Git, a commit in `jj` can have any number of parents. To produce a merge commit you create a new change whose parent list contains the tips of the branches you want to merge. The canonical way to do this is `jj new <rev1> <rev2> [...]`, which the official documentation describes as:

> Note that you can create a merge commit by specifying multiple revisions as argument. For example, `jj new @ main` will create a new commit with the working copy and the `main` bookmark as parents.

A colocated jj+git repository is already initialized at `/home/user/myrepo`. User identity is pre-configured. The starting history looks like this (newest at top):

```
@   (empty working copy on top of the branch_x tip)
|
*  Branch X commit   <-- bookmark: branch_x   (adds x.txt = "x")
|
|  *  Branch Y commit   <-- bookmark: branch_y   (adds y.txt = "y")
|/
*  Base commit                                   (adds shared.txt = "shared content")
```

The two branches modify disjoint files (`x.txt` vs `y.txt`) so the merge will not produce conflicts.

## Requirements
- Create a single new commit (a merge commit) with description exactly `Merge branches`.
- The merge commit must have exactly two parents: the tip of `branch_x` and the tip of `branch_y`.
- The merge commit must include the three data files at the expected contents:
  - `shared.txt` = `shared content`
  - `x.txt` = `x`
  - `y.txt` = `y`
- The `branch_x` and `branch_y` bookmarks must NOT be moved by this operation.

## Implementation Guide
1. `cd /home/user/myrepo`
2. Inspect the current history to confirm the divergence: `jj log`.
3. Create the merge commit by passing both bookmark names as the parents of the new change:
   ```bash
   jj new branch_x branch_y -m "Merge branches"
   ```
   This creates a new working-copy change whose parents are exactly the tips of `branch_x` and `branch_y`, and sets its description to `Merge branches`.
4. Verify the merge with:
   ```bash
   jj log -r 'description(substring:"Merge branches")' --no-graph -T 'description.first_line() ++ "\n"'
   jj log -r 'description(substring:"Merge branches")-' --no-graph -T 'description.first_line() ++ "\n"'
   ```
   The first command must print one line `Merge branches`. The second command must print exactly the two parent descriptions `Branch X commit` and `Branch Y commit` (in some order).

## Constraints
- Project path: /home/user/myrepo
- Use the real `jj` binary that is pre-installed in the environment. Do not mock or stub `jj`.
- Do not move, rename, or delete the `branch_x` or `branch_y` bookmarks.
- Do not modify the contents of `shared.txt`, `x.txt`, or `y.txt`.
- Use a single `jj new` invocation with multiple revsets to create the merge — do not synthesize the merge by manually editing files.
