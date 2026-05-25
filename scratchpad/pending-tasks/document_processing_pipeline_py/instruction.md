# Document Processing Pipeline (Hatchet, Python)

Build a [Hatchet](https://docs.hatchet.run) DAG workflow named `doc_pipeline` (Python) that processes a document through four sequential stages: `ingest` -> `ocr` -> `extract` -> `index`. The final `index` stage produces a JSON index describing the document.

A local Hatchet engine is already running inside the container and the standard Hatchet client environment variables (`HATCHET_CLIENT_TOKEN`, `HATCHET_CLIENT_HOST_PORT`, `HATCHET_CLIENT_TLS_STRATEGY=none`) are already exported.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Worker start command: `python3 worker.py` (registers and runs the `doc_pipeline` workflow on a Hatchet worker).
- Trigger command: `python3 run.py <doc_id> <content>` — triggers the `doc_pipeline` workflow with the given document, waits for it to complete, and prints the final `index` output as a single line of JSON to stdout, prefixed with `INDEX: ` (for example: `INDEX: {"doc_id": "...", "word_count": 5, "indexed_at": "..."}`).
- The `doc_pipeline` workflow must contain four DAG tasks named `ingest`, `ocr`, `extract`, and `index`, chained linearly with `ingest` -> `ocr` -> `extract` -> `index`.
- After a successful run for a given `<doc_id>`, the directory `/tmp/docs/<doc_id>/` must exist and contain exactly four artifact files (one per stage of the pipeline). The `index` stage's artifact MUST be a file named `index.json`.
- The `index.json` artifact must be valid JSON containing at least the keys `doc_id`, `word_count`, and `indexed_at`. `indexed_at` must be a valid ISO 8601 timestamp.
- Exit code of the trigger command is `0` on success.

