import { hatchet, workflow } from "./workflow.js";

const runId = process.env.ZEALT_RUN_ID || 'default-run-id';

async function main() {
  const worker = await hatchet.worker(`linear-dag-worker-${runId}`, {
    workflows: [workflow],
  });
  await worker.start();
}

main().catch(console.error);
