import * as fs from 'fs';
import { processOrder } from './task.js';

async function main() {
  const runId = process.env.ZEALT_RUN_ID || 'default';
  const logFile = `/tmp/orders-${runId}.log`;

  if (fs.existsSync(logFile)) {
    fs.truncateSync(logFile, 0);
  } else {
    fs.writeFileSync(logFile, '');
  }

  const regions = [
    `US-${runId}`,
    `US-${runId}`,
    `EU-${runId}`,
    `EU-${runId}`
  ];

  console.log(`Starting 4 runs for runId: ${runId}`);
  
  await Promise.all(regions.map(region => processOrder.run({ region })));
  
  console.log('All runs completed.');
}

main().catch(console.error);
