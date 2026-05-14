# Restore a Jujutsu Repository to a Past Operation

## Background
Jujutsu (`jj`) records every repository-modifying command in its **operation log** (`jj op log`). Each entry in the operation log has a stable operation ID, a human-readable operation description (e.g. `commit`, `new empty commit`, `abandon commit`), and an `args:` line that records the exact CLI invocation that produced the operation. Using `jj op restore <operation_id>` you can recover the repository view to exactly the state it had right after that operation, even after many subsequent commits, abandons, rebases, or other history rewrites.

A colocated jj + git repository is already initialized at `/home/user/myrepo`. User identity has been pre-configured globally. The repository has had a sequence of named operations performed on it. The CURRENT (visible) state of the repo is:

- A linear chain `Stage 1 -> Stage 3 -> extra1 -> extra2 -> @` where `@` is the empty working copy.
- `Stage 1` introduced `file1.txt` with content `content A`.
- `Stage 3` introduced `file3.txt` with content `content C`.
- `extra1` and `extra2` are empty commits made after `Stage 3`.
- There is **no** visible commit whose description contains `Stage 2`.
- The working copy on disk contains `file1.txt` and `file3.txt` but **not** `file2.txt`.

However, earlier in the history of operations, the repository did go through a state with a `Stage 2` commit that contained `file2.txt` with content `content B`. Specifically, the operation that committed `Stage 2` was a `jj commit -m "Stage 2"` operation. After that operation, a `Stage 3` commit was added, then `Stage 2` was abandoned (which rebased `Stage 3` onto `Stage 1` and removed `file2.txt` from history), and finally two empty commits (`extra1`, `extra2`) were created.

## Requirements
You must restore the repository to the **TARGET STATE** — the state that existed right after the `jj commit -m "Stage 2"` operation — using only `jj op log` and `jj op restore`. After restoring, the repository must satisfy ALL of the following:

1. The visible repository must contain exactly one commit whose description is `Stage 1` and exactly one commit whose description is `Stage 2`.
2. The visible repository must contain **no** commit whose description contains `Stage 3`.
3. The visible repository must contain **no** commit whose description contains `extra1` or `extra2`.
4. The file `/home/user/myrepo/file1.txt` must exist on disk in the working copy.
5. The file `/home/user/myrepo/file2.txt` must exist on disk in the working copy with content `content B` (a trailing newline is acceptable).
6. The file `/home/user/myrepo/file3.txt` must **not** exist on disk in the working copy.
7. The most recent operation in `jj op log` must be a `restore` operation, demonstrating that the restoration was performed via `jj op restore`.

## Implementation Guide
1. `cd /home/user/myrepo`.
2. Inspect the operation log to understand the history of operations:
   ```bash
   jj op log
   ```
   Each entry shows the operation ID, the operation description (e.g. `commit`, `new empty commit`, `abandon commit`, etc.), and an `args:` line with the exact CLI command that produced that operation.
3. Identify the operation that committed `Stage 2`. It is the operation whose **operation description** is `commit <commit_id>` and whose `args:` line is `args: jj commit -m 'Stage 2'` (jj may render the message with either single or double quotes depending on its shell-escaping rules; the human-readable description begins with the word `commit` rather than `snapshot working copy`). Note that there is typically a separate `snapshot working copy` operation immediately before the `commit` operation that shares the same `args:` line; you want the `commit` operation, **not** the `snapshot working copy` operation, because only the `commit` operation produces the full `Stage 1 -> Stage 2 -> @` state.
   You can also print operation IDs alongside the args by running:
   ```bash
   jj op log --no-graph -T 'self.id().short() ++ " | " ++ self.description() ++ "\n"'
   ```
   or with `-p` to see what each operation changed.
4. Copy the (short or full) operation ID of that operation. Any unambiguous prefix is enough.
5. Restore the repository to that operation:
   ```bash
   jj op restore <operation_id>
   ```
   This will create a new operation that restores the repo view to exactly the state at the `jj commit -m "Stage 2"` operation: `Stage 1 (file1.txt) -> Stage 2 (file2.txt) -> @ (empty)`. The working-copy files on disk will also be updated to reflect this restored state — `file2.txt` will reappear and `file3.txt` will be removed.
6. Verify with `jj log` and `ls /home/user/myrepo` that the restored state matches the requirements above.

## Constraints
- Project path: /home/user/myrepo
- Use the real `jj` binary that is pre-installed in the environment. Do NOT mock or stub `jj`.
- You MUST use `jj op log` to find the target operation and `jj op restore <op_id>` to restore. Do NOT use `jj undo` (which only reverts the single most recent operation and would not yield the correct multi-operation rollback), do NOT manually re-create the commits with `jj new`/`jj commit`, and do NOT manually create/delete files with shell commands to fake the state.
- Do not modify the user identity or global jj configuration.
