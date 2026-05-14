# Restore a Single File From an Earlier Revision With `jj restore`

## Background
You have a colocated Jujutsu (`jj`) repository at `/home/user/myrepo`. The repository contains two non-root commits in a linear stack, plus an empty working-copy commit on top:

1. The grand-parent commit `@--` has the description `Initial config` and creates `config.json` with the content:

   ```json
   {"version": "1.0"}
   ```

2. The parent commit `@-` has the description `Update config and add extras`. It modifies `config.json` to:

   ```json
   {"version": "2.0"}
   ```

   and creates a new file `extra.txt` with the content `additional data`.

3. The working copy `@` is an empty commit on top of `@-` (no description, no changes).

The user identity is already configured in the repo, and the `jj` binary is installed at `/usr/local/bin/jj`.

## Requirements
In the working copy `@`, restore **only** `config.json` to the version stored in the `Initial config` commit (`{"version": "1.0"}`). The file `extra.txt` must remain present in the working copy with its content `additional data`, and the `Update config and add extras` commit (`@-`) must NOT be modified.

After your changes:

- On disk in `/home/user/myrepo`, `config.json` must contain `{"version": "1.0"}`.
- On disk in `/home/user/myrepo`, `extra.txt` must still exist with content `additional data`.
- The parent commit `@-` (`Update config and add extras`) must still be the same change — it must still modify `config.json` to `{"version": "2.0"}` and add `extra.txt`.
- `jj diff -r '@'` must show `config.json` being reverted from `{"version": "2.0"}` to `{"version": "1.0"}` in the working copy.

## Implementation Guide
1. `cd /home/user/myrepo`.
2. Use `jj restore` to copy the version of `config.json` from the `Initial config` revision into the working copy:

   ```bash
   jj restore --from 'description(substring:"Initial config")' config.json
   ```

   The `--from <REVSET>` flag selects the source revision (the `Initial config` commit). When `--into` is omitted, `jj` restores into the working copy `@`. Passing the path `config.json` restricts the restore to that single file, leaving `extra.txt` untouched in `@`.
3. Verify with `jj diff -r '@'` and `cat config.json` / `cat extra.txt` that only `config.json` was reverted.

## Constraints
- Project path: /home/user/myrepo
- Use only the `jj` CLI; do not manually edit anything under `.jj/` or `.git/`.
- Do NOT abandon, rewrite, or `jj edit` the existing commits — `@-` (`Update config and add extras`) must remain unchanged, and the `Initial config` commit must still exist with its description.
- Do NOT delete `extra.txt`; it must still be present in the working copy after your changes.
- The change must live in the working copy `@` (i.e., `jj diff -r '@'` must show the revert of `config.json`).
