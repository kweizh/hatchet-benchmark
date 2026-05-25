# Pydantic-Typed Outputs in a 2-Step Hatchet DAG (Python SDK)

## Background
Hatchet is a distributed task queue and workflow engine focused on durable execution. Beyond returning plain dictionaries from tasks, the Hatchet **Python SDK** (`hatchet-sdk`) supports **statically typed inputs and outputs** by integrating with Pydantic. When a task is declared with a Pydantic `BaseModel` return type, downstream tasks can fetch the parent output as a fully validated Pydantic object via the context, instead of dealing with raw dictionaries.

In this task you will use the Hatchet Python SDK to build a 2-step linear DAG that uses **Pydantic models for both workflow input and the output of every task**. A first task parses a sentence into words, and a second task consumes the first task's typed output and produces a typed summary.

## Requirements
- Use the `hatchet-sdk` Python package (with `pydantic`) to connect to a real Hatchet server.
- Define the following Pydantic models in the project and use them as the workflow `input_validator` and each task's return type:
  - `StringInput(BaseModel)` with field `text: str`.
  - `ParsedOutput(BaseModel)` with fields `words: list[str]` and `word_count: int`.
  - `SummaryOutput(BaseModel)` with fields `first_word: str`, `last_word: str`, and `total: int`.
- Build a single workflow whose name is exactly `typed-summary-${ZEALT_RUN_ID}`, where `${ZEALT_RUN_ID}` is read from the environment variable `ZEALT_RUN_ID` at runtime. The workflow must use `StringInput` as its `input_validator`.
- The workflow must consist of exactly two tasks executed sequentially:
  - `parse`: receives the workflow `StringInput`, splits `text` on whitespace into a list of words, and returns a `ParsedOutput` whose `words` is that list and `word_count` is the number of words.
  - `summarize`: declares `parse` as its only parent, reads `parse`'s output as a fully validated Pydantic `ParsedOutput` object from the context (i.e., the typed parent-output API, not as a raw dict), and returns a `SummaryOutput` whose `first_word` is the first element of `words`, `last_word` is the last element of `words`, and `total` equals `word_count`.
- Register the workflow on a Hatchet worker and start the worker so that Hatchet can dispatch tasks to it.
- From the same project, trigger the workflow once with the input `{"text": "the quick brown fox"}`, wait for it to finish, and write its workflow run ID to a log file in the exact format `Workflow Run ID: <run_id>`.

## Implementation Hints
- Install dependencies with `pip3 install hatchet-sdk pydantic`.
- The Hatchet client reads `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` from the environment automatically; both are pre-set in the task environment.
- Create a workflow with `hatchet.workflow(name=..., input_validator=StringInput)` and attach tasks with the `@workflow.task(...)` decorator. Declare each task's return type annotation as the appropriate Pydantic model so Hatchet knows the typed output shape.
- Inside `summarize`, use the typed parent-output API on the Hatchet context to fetch `parse`'s result as a `ParsedOutput` instance (look for the `parsed=True` / typed flavor of `task_output` / `parent_output` exposed by the SDK), rather than parsing a raw dict.
- To execute the DAG end-to-end in one process, run the worker in a background thread and then trigger the workflow from the main thread using the workflow's `run` / `aio_run` method, which blocks until the run completes and returns the typed result.
- After the run completes, obtain the workflow run ID from the returned reference / context and append the line `Workflow Run ID: <run_id>` to `/home/user/myproject/output.log`.
- Read `ZEALT_RUN_ID` once at startup and reuse the same value when constructing the workflow name and when triggering the run.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The Hatchet workflow name must be `typed-summary-${ZEALT_RUN_ID}` where `ZEALT_RUN_ID` is read from the environment variable.
- The workflow has exactly 2 tasks composed as a linear DAG: `parse -> summarize`, where `summarize` declares `parents=[parse]` and reads `parse`'s output through the **typed** parent-output API on the Hatchet context.
- The workflow's `input_validator` is the `StringInput` Pydantic model, and each task's return type is the corresponding Pydantic model (`ParsedOutput` for `parse`, `SummaryOutput` for `summarize`).
- After running, the log file must contain a line in the exact format `Workflow Run ID: <run_id>` where `<run_id>` is the workflow run ID returned by Hatchet for the triggered run.
- When the workflow is triggered with `{"text": "the quick brown fox"}`, the final task (`summarize`) output must contain exactly: `first_word="the"`, `last_word="fox"`, and `total=4`.

