import { Hatchet } from '@hatchet-dev/typescript-sdk';
import * as fs from 'fs';

async function main() {
    const runId = process.env.ZEALT_RUN_ID;
    if (!runId) {
        throw new Error("ZEALT_RUN_ID is not set");
    }

    const cronName = `hb-cron-ts-${runId}`;
    const hatchet = Hatchet.init();

    // Define task
    const heartbeatTs = hatchet.task({
        name: 'heartbeatTs',
        fn: async (ctx) => {
            const timestamp = new Date().toISOString() + '\n';
            fs.appendFileSync('/tmp/heartbeats.log', timestamp);
            console.log('Heartbeat written:', timestamp.trim());
            return {};
        }
    });

    // Start worker
    const worker = await hatchet.worker('heartbeat-worker');
    await worker.registerWorkflow(heartbeatTs);
    worker.start(); // Do not await indefinitely

    // Register the cron
    const cron = await heartbeatTs.cron(cronName, '* * * * *', {});
    console.log('Cron registered with ID:', cron.metadata.id);

    // Wait ~75 seconds
    console.log('Waiting for cron to fire...');
    await new Promise(resolve => setTimeout(resolve, 75000));

    // Cleanup
    console.log('Deleting cron...');
    await hatchet.crons.delete(cron.metadata.id);
    
    console.log('Stopping worker...');
    await worker.stop();
    
    console.log('Done.');
    process.exit(0);
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
