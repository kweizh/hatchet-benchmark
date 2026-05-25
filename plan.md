# Evaluation Dataset Research: Hatchet

### 1. Library Overview

*   **Description**: Hatchet is a distributed task queue and workflow engine designed for modern, high-throughput applications. It focuses on **durable execution**, allowing developers to write background tasks and complex workflows as code with built-in support for retries, concurrency control, and state persistence.
*   **Ecosystem Role**: It serves as a more powerful alternative to simple task queues (like Celery or BullMQ) and a more developer-friendly alternative to heavy workflow engines (like Temporal or Airflow). It is particularly popular for AI agent orchestration and real-time data pipelines.
*   **Project Setup**:
    1.  **CLI Installation**: `curl -fsSL https://install.hatchet.run/install.sh | bash`
    2.  **Authentication**: `hatchet profile add` (requires an API token from Hatchet Cloud).
    3.  **Local Development**: Use `hatchet quickstart` to generate a boilerplate or `hatchet worker dev` to start a worker with hot-reloading.
    4.  **Environment Variables**: `HATCHET_CLIENT_TOKEN` is required for worker/client authentication.
    5.  **Server Address**: Always use the Hatchet Cloud, and the server address is the default value in SDKs, so no need to specify.

---

### 2. Core Primitives & APIs

*   **Tasks**: The basic unit of work, defined as a function.
    *   **Python**: `@hatchet.task(name=\"my-task\", retries=3)`
    *   **TypeScript**: `hatchet.task({ name: 'my-task', fn: async (input) => { ... } })`
*   **Workflows (DAGs)**: A collection of tasks with defined dependencies.
    *   **TypeScript Example**:
        ```typescript
        const dag = hatchet.workflow({ name: 'my-dag' });
        const step1 = dag.task({ name: 'step1', fn: async () => ({ data: 'hello' }) });
        const step2 = dag.task({ name: 'step2', parents: [step1], fn: async (input, ctx) => {
            const result = ctx.parentOutput(step1);
            return { msg: `${result.data} world` };
        }});
        ```
*   **Durable Execution**: Methods to pause and resume execution safely.
    *   `ctx.sleep(\"10s\")`: Pauses the task durably without holding worker resources.
    *   `ctx.waitFor(Or({ eventKey: \"user:input\" }, { sleepFor: \"5m\" }))`: Waits for an external event or a timeout.
*   **Child Spawning**: Dynamically triggering new workflows from within a task.
    *   `await ctx.spawnChild(childWorkflow, { ... })`
*   **Concurrency & Rate Limiting**:
    *   `concurrency: { limit: 10, key: (input) => input.userId }`: Limits concurrent runs per user.

**Documentation Links**:
*   [Core Concepts](https://docs.hatchet.run/v1/tasks)
*   [DAGs (Directed Acyclic Graphs)](https://docs.hatchet.run/v1/directed-acyclic-graphs)
*   [Child Spawning](https://docs.hatchet.run/v1/child-spawning)
*   [Concurrency Control](https://docs.hatchet.run/v1/concurrency)

---

### 3. Real-World Use Cases & Templates

*   **AI Agent Orchestration**: Managing long-running LLM calls, handling tool-use retries, and maintaining agent state across failures.
*   **Document Processing Pipelines**: A multi-stage DAG (Ingest -> OCR -> Extract -> Index) where each document or page can be fanned out as a child workflow.
    *   [Cookbook: Document Processing](https://docs.hatchet.run/cookbooks/document-processing)
*   **SaaS Background Jobs**: Sending transactional emails, generating reports, and handling webhooks with high reliability.
*   **Example Repository**: [Hatchet Python Examples](https://github.com/hatchet-dev/hatchet/tree/main/sdks/python/examples)

---

### 4. Developer Friction Points

*   **Dependency Injection & Circular Imports**: In Python/FastAPI or TypeScript/NestJS, the need to import task/workflow objects to trigger them often leads to circular dependency issues. Developers struggle to decouple the \"triggering\" code from the \"worker\" code.
*   **Worker Slot Management**: Understanding the relationship between `slots` (local worker capacity) and global concurrency limits is a common source of confusion when scaling high-concurrency fan-outs.
*   **Self-Hosting Complexity**: Configuring gRPC, TLS strategies, and PostgreSQL connection pooling for the Hatchet Engine in production environments is often cited as a challenge.
    *   [Issue: Worker locks up in certain runtimes](https://github.com/hatchet-dev/hatchet/issues/1804)
    *   [Discussion: Payload size limits](https://github.com/hatchet-dev/hatchet/discussions/1400)

---

### 5. Evaluation Ideas

1.  **Basic Reliability**: Implement a task that fetches data from a flaky API with a custom exponential backoff retry policy.
2.  **Linear DAG**: Create a 3-step sequence where each step transforms data from the previous one using `ctx.parentOutput`.
3.  **Dynamic Fan-out**: Build a workflow that takes a list of URLs, spawns a child task for each to scrape content, and aggregates the results in a final step.
4.  **Durable Sleep & Event Wait**: Implement a \"User Onboarding\" flow that sends a welcome email, waits 3 days for a \"profile_completed\" event, and sends a reminder if the event isn't received.
5.  **Concurrency Control**: Set up a task that processes payments and ensure no more than 1 payment per `userId` can be processed simultaneously.
6.  **AI Agent Loop**: Create a durable task that loops through LLM calls, using `ctx.sleep` between retries and persisting the \"conversation history\" in the task output.
7.  **Rate Limiting**: Configure a workflow that interacts with an external API (e.g., OpenAI) and strictly adheres to a \"100 requests per minute\" global rate limit.

---

### 6. Sources

1.  [Hatchet Official Documentation](https://docs.hatchet.run) - Primary source for concepts and API.
2.  [Hatchet GitHub Repository](https://github.com/hatchet-dev/hatchet) - Source code, examples, and issues.
3.  [Hatchet Blog: Durable Execution](https://hatchet.run/blog/durable-execution) - Deep dive into core philosophy.
4.  [Hatchet llms-full.txt](https://docs.hatchet.run/llms-full.txt) - Comprehensive technical overview for LLMs.
5.  [GitHub Discussions & Issues](https://github.com/hatchet-dev/hatchet/discussions) - Community feedback and friction points.