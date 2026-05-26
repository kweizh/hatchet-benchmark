import fs from 'node:fs';
import { processOrder, getLogPath, getRunId } from './hatchet.js';

const main = async () => {
  const runId = getRunId();
  const logPath = getLogPath();

  fs.writeFileSync(logPath, '');

  const usRegion = `US-${runId}`;
  const euRegion = `EU-${runId}`;

  await Promise.all([
    processOrder.run({ region: usRegion }),
    processOrder.run({ region: usRegion }),
    processOrder.run({ region: euRegion }),
    processOrder.run({ region: euRegion }),
  ]);
};

main().catch((error) => {
  console.error('Runner failed:', error);
  process.exit(1);
});
