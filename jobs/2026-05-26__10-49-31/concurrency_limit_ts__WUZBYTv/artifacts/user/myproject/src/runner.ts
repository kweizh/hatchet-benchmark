import fs from 'fs';
import { hatchet, processOrder } from './task.js';

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error('ZEALT_RUN_ID environment variable is required');
  }

  const logFile = `/tmp/orders-${runId}.log`;

  // Truncate the log file for a clean trial
  fs.writeFileSync(logFile, '');

  const usRegion = `US-${runId}`;
  const euRegion = `EU-${runId}`;

  console.log(`Submitting 4 runs: 2x ${usRegion}, 2x ${euRegion}`);

  await Promise.all([
    processOrder.run({ region: usRegion }),
    processOrder.run({ region: usRegion }),
    processOrder.run({ region: euRegion }),
    processOrder.run({ region: euRegion }),
  ]);

  console.log('All 4 runs completed.');
  console.log(`Log file: ${logFile}`);

  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
