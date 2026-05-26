import { Hatchet } from '@hatchet-dev/typescript-sdk';

const hatchet = Hatchet.init();
const runId = process.env.ZEALT_RUN_ID || 'local';

export const workflow = hatchet.workflow({
  name: `linear-dag-${runId}`,
  on: {
    event: 'linear:trigger',
  },
});

const step1 = workflow.task({
  name: 'step1',
  fn: async (input, ctx) => {
    return { text: 'hello' };
  },
});

const step2 = workflow.task({
  name: 'step2',
  parents: [step1],
  fn: async (input, ctx) => {
    const step1Output = await ctx.parentOutput(step1);
    return { text: step1Output.text + ' world' };
  },
});

const step3 = workflow.task({
  name: 'step3',
  parents: [step2],
  fn: async (input, ctx) => {
    const step2Output = await ctx.parentOutput(step2);
    return { final: step2Output.text + '!' };
  },
});
