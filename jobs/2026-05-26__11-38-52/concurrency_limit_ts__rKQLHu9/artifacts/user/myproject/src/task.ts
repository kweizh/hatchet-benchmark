import { Hatchet } from '@hatchet-dev/typescript-sdk';
import * as fs from 'fs';

const hatchet = Hatchet.init();

export const processOrder = hatchet.task({
  name: 'processOrder',
  concurrency: {
    expression: 'input.region',
    maxRuns: 1,
  },
  fn: async (input: { region: string }) => {
    const region = input.region;
    const runId = process.env.ZEALT_RUN_ID || 'default';
    const logFile = `/tmp/orders-${runId}.log`;
    
    fs.appendFileSync(logFile, `start ${region} ${Date.now()}\n`);
    await new Promise(resolve => setTimeout(resolve, 1500));
    fs.appendFileSync(logFile, `end ${region} ${Date.now()}\n`);
    
    return { success: true };
  }
});
