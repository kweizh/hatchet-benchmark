import { hatchet, workflow } from "./workflow.js";

const runId = process.env.ZEALT_RUN_ID ?? "default";

async function main() {
  const worker = await hatchet.worker(`linear-dag-worker-${runId}`, {
    workflows: [workflow],
  });

  await worker.start();
}

main().catch((err) => {
  console.error("Worker error:", err);
  process.exit(1);
});
