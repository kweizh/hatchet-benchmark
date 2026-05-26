import { Hatchet } from '@hatchet-dev/typescript-sdk';
import * as fs from 'fs';

const runId = process.env.ZEALT_RUN_ID || 'test';

const hatchet = Hatchet.init();

const childTask = hatchet.task({
  name: `square-item-${runId}`,
  fn: async (input: { n: number }) => {
    return { square: input.n * input.n };
  }
});

const parentTask = hatchet.task({
  name: `process-batch-${runId}`,
  fn: async (input: { items: number[] }) => {
    const promises = input.items.map(n => childTask.run({ n }));
    const results = await Promise.all(promises);
    return { squares: results.map(r => r.square) };
  }
});

async function main() {
  const worker = await hatchet.worker(`worker-${runId}`);
  await worker.registerWorkflow(childTask);
  await worker.registerWorkflow(parentTask);
  
  worker.start();
  
  console.log("Worker started, triggering parent task...");
  const result = await parentTask.run({ items: [1, 2, 3, 4, 5] });
  
  fs.writeFileSync('/tmp/result.json', JSON.stringify(result));
  console.log("Result written to /tmp/result.json");
  
  await worker.stop();
  process.exit(0);
}

main().catch(console.error);
