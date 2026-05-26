import { Hatchet } from '@hatchet-dev/typescript-sdk';
import fs from 'fs';

const runId = process.env.ZEALT_RUN_ID;
if (!runId) {
  console.error('ZEALT_RUN_ID environment variable is not set');
  process.exit(1);
}

const hatchet = Hatchet.init();

const childTask = hatchet.task({
  name: `square-item-${runId}`,
  fn: async (input: { n: number }) => {
    console.log(`Squaring ${input.n}`);
    return { square: input.n * input.n };
  },
});

const parentTask = hatchet.task({
  name: `process-batch-${runId}`,
  fn: async (input: { items: number[] }) => {
    console.log(`Processing items: ${input.items}`);
    const promises = input.items.map((n: number) =>
      childTask.run({ n })
    );
    const results = await Promise.all(promises);
    return { squares: results.map((r: any) => r.square) };
  },
});

async function main() {
  console.log('Initializing worker...');
  const worker = await hatchet.worker('batch-worker', {
    workflows: [parentTask, childTask],
  });

  console.log('Starting worker in background...');
  const workerPromise = worker.start();

  console.log('Waiting for worker to be ready...');
  await worker.waitUntilReady();
  console.log('Worker is ready.');

  try {
    console.log('Triggering parent task...');
    const workflowRun = await hatchet.admin.runWorkflow(`process-batch-${runId}`, {
      items: [1, 2, 3, 4, 5],
    });

    console.log('Waiting for result...');
    const result = await workflowRun.result();
    console.log('Result received:', result);

    // Extract the result from the task name key
    const taskName = `process-batch-${runId}`;
    const finalResult = result[taskName];

    fs.writeFileSync('/tmp/result.json', JSON.stringify(finalResult));
    console.log('Result written to /tmp/result.json');
  } catch (e) {
    console.error('Error during execution:', e);
    process.exit(1);
  } finally {
    console.log('Stopping worker...');
    await worker.stop();
    await workerPromise;
    console.log('Worker stopped.');
    process.exit(0);
  }
}

main().catch((err) => {
  console.error('Unhandled error in main:', err);
  process.exit(1);
});
