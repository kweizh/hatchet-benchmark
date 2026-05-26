import fs from 'node:fs';
import { HatchetClient } from '@hatchet-dev/typescript-sdk';

type ProcessOrderInput = {
  region: string;
};

const hatchet = HatchetClient.init();

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const getRunId = () => {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error('ZEALT_RUN_ID is required');
  }

  return runId;
};

const getLogPath = () => `/tmp/orders-${getRunId()}.log`;

const processOrder = hatchet.task<ProcessOrderInput, void>({
  name: 'processOrder',
  concurrency: {
    expression: 'input.region',
    maxRuns: 1,
  },
  fn: async (input) => {
    const logPath = getLogPath();
    const startTime = Date.now();
    fs.appendFileSync(logPath, `start ${input.region} ${startTime}\n`);
    await sleep(1500);
    const endTime = Date.now();
    fs.appendFileSync(logPath, `end ${input.region} ${endTime}\n`);
  },
});

export { hatchet, processOrder, getRunId, getLogPath };
