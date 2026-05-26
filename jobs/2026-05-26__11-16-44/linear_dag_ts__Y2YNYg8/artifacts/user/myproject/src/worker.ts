import { hatchet, runId, workflow } from "./workflow.js";

const workerName = `linear-dag-worker-${runId}`;

const worker = hatchet.worker(workerName, { workflows: [workflow] });

await worker.start();
