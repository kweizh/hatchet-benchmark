import Hatchet from '@hatchet-dev/typescript-sdk';
import fs from 'fs';

const hatchet = Hatchet.init();

const runId = process.env.ZEALT_RUN_ID || 'default';
const logFile = `/tmp/orders-${runId}.log`;

const processOrder = hatchet.task({
  name: 'processOrder',
  concurrency: {
    name: 'order-region-concurrency',
    expression: 'input.region',
    maxRuns: 1,
  },
  fn: async (input: { region: string }) => {
    const { region } = input;
    
    // Append start log
    fs.appendFileSync(logFile, `start ${region} ${Date.now()}\n`);
    
    // Sleep 1.5 seconds
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    // Append end log
    fs.appendFileSync(logFile, `end ${region} ${Date.now()}\n`);
    
    return { status: 'completed', region };
  },
});

async function main() {
  const worker = await hatchet.worker('order-worker');
  await worker.register([processOrder]);
  console.log('Worker started and task registered');
  await worker.start();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
