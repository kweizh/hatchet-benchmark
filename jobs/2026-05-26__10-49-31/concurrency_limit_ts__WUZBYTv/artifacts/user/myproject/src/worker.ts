import { hatchet, processOrder } from './task.js';

async function main() {
  const worker = await hatchet.worker('order-processing-worker');

  await worker.registerWorkflows([processOrder]);

  await worker.start();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
