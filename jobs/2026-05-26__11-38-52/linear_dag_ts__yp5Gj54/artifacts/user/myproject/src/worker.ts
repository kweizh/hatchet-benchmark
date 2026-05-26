import { hatchet, workflow } from './workflow.js';

const runId = process.env.ZEALT_RUN_ID || 'default';
const workerName = `linear-dag-worker-${runId}`;

async function main() {
  const worker = await hatchet.worker(workerName, {
    workflows: [workflow]
  });
  await worker.start();
}

main().catch(console.error);
