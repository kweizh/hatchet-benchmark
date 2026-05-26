import fs from 'fs';
import Hatchet from '@hatchet-dev/typescript-sdk';

const hatchet = Hatchet.init();

export type OrderInput = {
  region: string;
};

export const processOrder = hatchet.task<OrderInput>({
  name: 'processOrder',
  executionTimeout: '60s',
  concurrency: {
    expression: 'input.region',
    maxRuns: 1,
  },
  fn: async (input) => {
    const runId = process.env.ZEALT_RUN_ID ?? 'default';
    const logFile = `/tmp/orders-${runId}.log`;
    const { region } = input;

    fs.appendFileSync(logFile, `start ${region} ${Date.now()}\n`);

    await new Promise<void>((resolve) => setTimeout(resolve, 1500));

    fs.appendFileSync(logFile, `end ${region} ${Date.now()}\n`);
  },
});

export { hatchet };
