# Split a Jujutsu Commit into Two by File Paths

## Background
You have a colocated Jujutsu (`jj`) repository at `/home/user/myrepo`. The repository currently contains a single non-root commit whose description is `Combined changes`. That commit touches **two** files in the project root:

- `feature_a.py` with the content:

  ```python
  def a(): return "a"
  ```

- `feature_b.py` with the content:

  ```python
  def b(): return "b"
  ```

The working-copy commit `@` is an empty child of the `Combined changes` commit. The user identity is already configured and the `jj` binary is installed at `/usr/local/bin/jj`.

## Requirements
Split the `Combined changes` commit into TWO separate commits using `jj split` in **non-interactive** mode (by passing file path filesets, not a diff editor):

1. A commit whose description is exactly `Feature A` and whose only changed file is `feature_a.py`.
2. A commit whose description is exactly `Feature B` and whose only changed file is `feature_b.py`.
3. The `Feature A` commit must be the **parent** of the `Feature B` commit (i.e. they form a linear stack `Feature A → Feature B`, not parallel siblings).
4. The original `Combined changes` commit must no longer exist as such — it was *split*, not kept alongside the new commits.
5. The contents of `feature_a.py` and `feature_b.py` on disk must be unchanged.

## Implementation Guide
1. `cd /home/user/myrepo`
2. Inspect the repo to find the `Combined changes` commit, e.g. with `jj log` or by using the revset `description(substring:"Combined changes")`.
3. Use `jj split` non-interactively by passing `feature_a.py` as a fileset argument and a description via `-m`. For example:

   ```bash
   jj split -r 'description(substring:"Combined changes")' feature_a.py -m "Feature A"
   ```

   Because filesets are provided, `jj split` will NOT open an interactive diff editor. The *selected* commit (containing `feature_a.py`) gets the description `Feature A`. The *remaining* commit (containing `feature_b.py`) keeps the original description `Combined changes` and becomes a child of the selected commit. Do **not** pass `--parallel`/`-p`; the two new commits must form a parent/child stack.
4. Rename the remaining commit from `Combined changes` to `Feature B`, for example:

   ```bash
   jj describe -r 'description(substring:"Combined changes")' -m "Feature B"
   ```
5. Verify with `jj log` that you now have two non-root, non-empty commits: `Feature A` (containing only `feature_a.py`) and `Feature B` (containing only `feature_b.py`), with `Feature A` as the parent of `Feature B`. No commit with description `Combined changes` should remain.

## Constraints
- Project path: /home/user/myrepo
- Use only the `jj` CLI; do not manually edit `.jj/` or `.git/` internals.
- Do NOT use `jj split --parallel` / `-p` — the two resulting commits must form a parent/child stack.
- Do NOT change the contents of `feature_a.py` or `feature_b.py`.
- The descriptions must be exactly `Feature A` and `Feature B` (no extra whitespace, no trailing punctuation).
- No commit with description `Combined changes` may remain in the repository.
