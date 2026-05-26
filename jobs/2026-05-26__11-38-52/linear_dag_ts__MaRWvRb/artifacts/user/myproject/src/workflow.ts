import { Hatchet } from "@hatchet-dev/typescript-sdk";

export const hatchet = new Hatchet();

const runId = process.env.ZEALT_RUN_ID || 'default-run-id';

export const workflow = hatchet.workflow({
  name: `linear-dag-${runId}`,
});

export const step1 = workflow.task({
  name: "step1",
  fn: async (input, ctx) => {
    return { text: "hello" };
  },
});

export const step2 = workflow.task({
  name: "step2",
  parents: [step1],
  fn: async (input, ctx) => {
    console.log("ctx keys:", Object.keys(ctx));
    const parent = await ctx.parentOutput(step1);
    return { text: parent.text + " world" };
  },
});

export const step3 = workflow.task({
  name: "step3",
  parents: [step2],
  fn: async (input, ctx) => {
    const parent = await ctx.parentOutput(step2);
    return { final: parent.text + "!" };
  },
});
