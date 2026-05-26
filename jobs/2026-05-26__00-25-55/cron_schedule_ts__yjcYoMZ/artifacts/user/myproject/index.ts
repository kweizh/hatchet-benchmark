import Hatchet from '@hatchet-dev/typescript-sdk';
import fs from 'fs';

const hatchet = Hatchet.init();

const ZEALT_RUN_ID = process.env.ZEALT_RUN_ID || 'manual';
const cronName = `hb-cron-ts-${ZEALT_RUN_ID}`;
const logFile = '/tmp/heartbeats.log';

// Define the task using hatchet.task
const heartbeatTs = hatchet.task({
  name: 'heartbeatTs',
  fn: async (input, ctx) => {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(logFile, `${timestamp}\n`);
    console.log(`[${timestamp}] Heartbeat recorded.`);
    return { success: true };
  },
});

async function main() {
  try {
    console.log('Starting worker...');
    const worker = await hatchet.worker('heartbeat-worker');
    
    // Register the standalone task
    await worker.registerWorkflow(heartbeatTs);
    
    // Start worker
    worker.start();
    
    // Wait until worker is ready
    console.log('Waiting for worker to be ready...');
    await worker.waitUntilReady();
    console.log('Worker is ready.');

    console.log(`Registering cron trigger: ${cronName}`);
    // Use the .cron() method on the task object
    const cronTrigger = await heartbeatTs.cron(cronName, '* * * * *', {});
    const cronId = cronTrigger.metadata.id;
    console.log(`Cron trigger registered with ID: ${cronId}`);

    console.log('Waiting 75 seconds for at least one tick...');
    await new Promise((resolve) => setTimeout(resolve, 75000));

    console.log('75 seconds elapsed. Cleaning up...');

    // Delete the cron trigger
    await hatchet.crons.delete(cronId);
    console.log(`Cron trigger ${cronId} deleted.`);

    // Stop the worker
    await worker.stop();
    console.log('Worker stopped.');
    
    process.exit(0);
  } catch (error) {
    console.error('Error in main loop:', error);
    process.exit(1);
  }
}

main();
