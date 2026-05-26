import { writeFile } from "node:fs/promises";
import { HatchetClient } from "@hatchet-dev/typescript-sdk";

type SquareInput = {
  n: number;
};

type SquareOutput = {
  square: number;
};

type BatchInput = {
  items: number[];
};

type BatchOutput = {
  squares: number[];
};

const runId = process.env.ZEALT_RUN_ID;

if (!runId) {
  throw new Error("ZEALT_RUN_ID is required to name Hatchet tasks.");
}

const hatchet = HatchetClient.init();

const squareTask = hatchet.task<SquareInput, SquareOutput>({
  name: `square-item-${runId}`,
  fn: async (input) => ({
    square: input.n * input.n,
  }),
});

const processBatch = hatchet.task<BatchInput, BatchOutput>({
  name: `process-batch-${runId}`,
  fn: async (input) => {
    const results = await Promise.all(
      input.items.map((item) => squareTask.run({ n: item }))
    );

    return {
      squares: results.map((result) => result.square),
    };
  },
});

async function main() {
  const worker = await hatchet.worker(`dynamic-fanout-worker-${runId}`, {
    workflows: [processBatch, squareTask],
    slots: 100,
  });

  const workerStart = worker.start();
  await worker.waitUntilReady();

  const result = await processBatch.run({ items: [1, 2, 3, 4, 5] });

  await writeFile("/tmp/result.json", JSON.stringify(result));

  await worker.stop();
  await workerStart;
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => {
    process.exit();
  });
