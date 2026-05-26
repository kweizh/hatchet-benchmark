import { Hatchet } from '@hatchet-dev/typescript-sdk';
import { processOrder } from './task.js';

const hatchet = Hatchet.init();

async function main() {
  const worker = await hatchet.worker('order-worker');
  await worker.registerWorkflow(processOrder);
  worker.start();
  console.log('Worker started');
}

main().catch(console.error);
