import Hatchet from '@hatchet-dev/typescript-sdk';
import * as fs from 'fs';

const ZEALT_RUN_ID = process.env.ZEALT_RUN_ID;
if (!ZEALT_RUN_ID) {
  throw new Error('ZEALT_RUN_ID environment variable is not set');
}

const LOG_FILE = '/tmp/heartbeats.log';
const CRON_NAME = `hb-cron-ts-${ZEALT_RUN_ID}`;
const CRON_EXPRESSION = '* * * * *';
const RUN_DURATION_MS = 75_000;

const hatchet = Hatchet.init();

// Define the heartbeat task
const heartbeatTs = hatchet.task({
  name: 'heartbeatTs',
  fn: async (_input: Record<string, unknown>) => {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(LOG_FILE, timestamp + '\n');
    console.log(`[heartbeatTs] Appended timestamp: ${timestamp}`);
  },
});

async function main() {
  console.log(`[main] Starting heartbeat worker. CRON_NAME=${CRON_NAME}`);

  // Create the worker first
  const worker = await hatchet.worker('heartbeat-worker', {
    workflows: [heartbeatTs],
  });

  // Start the worker without awaiting its lifetime
  worker.start().catch((err: Error) => {
    console.error('[main] Worker error:', err);
  });

  // Give the worker a moment to register
  await new Promise((resolve) => setTimeout(resolve, 3000));

  // Create the cron trigger
  console.log(`[main] Creating cron trigger: ${CRON_NAME}`);
  const cronJob = await heartbeatTs.cron(CRON_NAME, CRON_EXPRESSION, {});
  const cronId = cronJob.metadata.id;
  console.log(`[main] Cron trigger created with ID: ${cronId}`);

  // Wait for ~75 seconds to allow at least one cron tick to be processed
  console.log(`[main] Waiting ${RUN_DURATION_MS / 1000}s for cron execution...`);
  await new Promise((resolve) => setTimeout(resolve, RUN_DURATION_MS));

  // Delete the cron trigger
  console.log(`[main] Deleting cron trigger: ${cronId}`);
  await hatchet.crons.delete(cronId);
  console.log('[main] Cron trigger deleted.');

  // Stop the worker
  await worker.stop();
  console.log('[main] Worker stopped. Exiting.');

  process.exit(0);
}

main().catch((err) => {
  console.error('[main] Fatal error:', err);
  process.exit(1);
});
