import { hatchet, processOrder } from './hatchet.js';

const main = async () => {
  const worker = await hatchet.worker('process-order-worker', {
    workflows: [processOrder],
    slots: 10,
  });

  await worker.start();
};

main().catch((error) => {
  console.error('Worker failed to start:', error);
  process.exit(1);
});
