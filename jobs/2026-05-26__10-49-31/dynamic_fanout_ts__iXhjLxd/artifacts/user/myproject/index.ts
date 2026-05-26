import { HatchetClient } from '@hatchet-dev/typescript-sdk/v1';
import fs from 'fs';

const runId = process.env.ZEALT_RUN_ID;
if (!runId) {
  throw new Error('ZEALT_RUN_ID environment variable is required');
}

const childTaskName = `square-item-${runId}`;
const parentTaskName = `process-batch-${runId}`;

console.log(`Using task names: child="${childTaskName}", parent="${parentTaskName}"`);

const hatchet = HatchetClient.init();

// Child task: accepts { n: number }, returns { square: number }
const squareItemTask = hatchet.task({
  name: childTaskName,
  fn: async (input: { n: number }) => {
    return {
      square: input.n * input.n,
    };
  },
});

// Parent task: accepts { items: number[] }, fans out to child tasks, returns { squares: number[] }
const processBatchTask = hatchet.task({
  name: parentTaskName,
  fn: async (input: { items: number[] }) => {
    const promises = input.items.map((n) => squareItemTask.run({ n }));
    const results = await Promise.all(promises);
    const squares = results.map((r) => r.square);
    return { squares };
  },
});

async function main() {
  // Start the worker with both tasks registered
  const worker = await hatchet.worker(`fanout-worker-${runId}`, {
    workflows: [squareItemTask, processBatchTask],
    slots: 100,
  });

  console.log('Starting worker...');
  // Start worker in background (non-blocking)
  worker.start();

  // Wait until the worker is ready and registered with Hatchet Cloud
  console.log('Waiting for worker to be ready...');
  await worker.waitUntilReady(30000);

  console.log('Triggering parent task with items [1,2,3,4,5]...');
  const result = await processBatchTask.run({ items: [1, 2, 3, 4, 5] });

  console.log('Result:', JSON.stringify(result));

  // Write result to /tmp/result.json
  fs.writeFileSync('/tmp/result.json', JSON.stringify(result));
  console.log('Written result to /tmp/result.json');

  // Shut down the worker cleanly
  await worker.stop();
  console.log('Worker stopped. Exiting.');
  process.exit(0);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
