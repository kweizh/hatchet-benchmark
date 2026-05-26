import { Hatchet } from '@hatchet-dev/typescript-sdk';
import { workflow } from './workflow';

const hatchet = Hatchet.init();
const runId = process.env.ZEALT_RUN_ID || 'local';

async function main() {
  const worker = await hatchet.worker(`linear-dag-worker-${runId}`, {
    workflows: [workflow],
  });
  await worker.start();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
