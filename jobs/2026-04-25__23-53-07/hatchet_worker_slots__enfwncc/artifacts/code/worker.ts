import { Hatchet } from '@hatchet-dev/typescript-sdk';

const hatchet = Hatchet.init();

const StandardSleepWorkflow = hatchet.workflow({
  name: 'standard',
  on: {
    event: 'standard:sleep',
  },
  steps: [
    {
      name: 'step',
      run: async (ctx) => {
        console.log('StandardSleepTask started, holding slot...');
        await new Promise((resolve) => setTimeout(resolve, 5000));
        console.log('StandardSleepTask finished.');
        return { status: 'completed' };
      },
    },
  ],
});

const DurableSleepWorkflow = hatchet.workflow({
  name: 'durable',
  on: {
    event: 'durable:sleep',
  },
  steps: [
    {
      name: 'step',
      run: async (ctx) => {
        console.log('DurableSleepTask started, releasing slot...');
        await ctx.sleepFor('5s');
        console.log('DurableSleepTask finished.');
        return { status: 'completed' };
      },
    },
  ],
});

const TestWorkflow = hatchet.workflow({
  name: 'test',
  on: {
    event: 'test:task',
  },
  steps: [
    {
      name: 'step',
      run: async (ctx) => {
        console.log('TestTask executed!');
        return { status: 'executed' };
      },
    },
  ],
});

async function main() {
  const worker = await hatchet.worker('slot-worker', {
    maxRuns: 1,
  });

  await worker.registerWorkflow(StandardSleepWorkflow);
  await worker.registerWorkflow(DurableSleepWorkflow);
  await worker.registerWorkflow(TestWorkflow);

  console.log('Worker started with concurrency limit 1...');
  await worker.start();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
