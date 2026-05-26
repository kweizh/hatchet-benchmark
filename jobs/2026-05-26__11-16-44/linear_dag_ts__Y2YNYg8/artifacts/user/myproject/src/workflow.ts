import { Hatchet } from "@hatchet-dev/typescript-sdk";

const runId = process.env.ZEALT_RUN_ID ?? "unknown";
const workflowName = `linear-dag-${runId}`;

const hatchet = new Hatchet();

const workflow = hatchet.workflow({ name: workflowName });

const step1 = workflow.task({
  name: "step1",
  fn: async () => ({ text: "hello" }),
});

const step2 = workflow.task({
  name: "step2",
  parents: [step1],
  fn: async (ctx) => {
    const parent = await ctx.parentOutput(step1);
    return { text: `${parent.text} world` };
  },
});

const step3 = workflow.task({
  name: "step3",
  parents: [step2],
  fn: async (ctx) => {
    const parent = await ctx.parentOutput(step2);
    return { final: `${parent.text}!` };
  },
});

export { hatchet, runId, workflow, workflowName, step3 };
