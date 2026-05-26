import Hatchet from "@hatchet-dev/typescript-sdk";

const runId = process.env.ZEALT_RUN_ID ?? "default";

export const hatchet = new Hatchet();

export const workflow = hatchet.workflow<{}, {
  step1: { text: string };
  step2: { text: string };
  step3: { final: string };
}>({
  name: `linear-dag-${runId}`,
});

export const step1 = workflow.task({
  name: "step1",
  fn: async (_input, _ctx) => {
    return { text: "hello" };
  },
});

export const step2 = workflow.task({
  name: "step2",
  parents: [step1],
  fn: async (_input, ctx) => {
    const parent = await ctx.parentOutput(step1);
    return { text: parent.text + " world" };
  },
});

export const step3 = workflow.task({
  name: "step3",
  parents: [step2],
  fn: async (_input, ctx) => {
    const parent = await ctx.parentOutput(step2);
    return { final: parent.text + "!" };
  },
});
