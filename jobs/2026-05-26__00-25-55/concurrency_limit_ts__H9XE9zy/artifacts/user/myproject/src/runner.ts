import Hatchet from '@hatchet-dev/typescript-sdk';
import fs from 'fs';

const hatchet = Hatchet.init();

const runId = process.env.ZEALT_RUN_ID;
if (!runId) {
  console.error('ZEALT_RUN_ID environment variable is required');
  process.exit(1);
}

const logFile = `/tmp/orders-${runId}.log`;

async function main() {
  // Truncate log file
  fs.writeFileSync(logFile, '');
  console.log(`Truncated log file: ${logFile}`);

  const regions = [
    `US-${runId}`,
    `US-${runId}`,
    `EU-${runId}`,
    `EU-${runId}`,
  ];

  console.log(`Firing 4 runs for regions: ${regions.join(', ')}`);

  try {
    const runs = regions.map((region) =>
      hatchet.admin.run_workflow('processOrder', { region })
    );

    const results = await Promise.all(runs);
    console.log('All runs triggered, waiting for completion...');
    
    await Promise.all(results.map(run => run.result()));
    console.log('All runs completed');
  } catch (err) {
    console.error('Error running tasks:', err);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
