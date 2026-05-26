import { HatchetClient } from "@hatchet-dev/typescript-sdk";
import { promises as fs } from "fs";

const hatchet = HatchetClient.init();

const heartbeatTask = hatchet.task({
  name: "heartbeatTs",
  fn: async () => {
    const timestamp = new Date().toISOString();
    await fs.appendFile("/tmp/heartbeats.log", `${timestamp}\n`);
  },
});

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const runId = process.env.ZEALT_RUN_ID;
if (!runId) {
  throw new Error("ZEALT_RUN_ID is required");
}

const cronName = `hb-cron-ts-${runId}`;

const main = async () => {
  let workerPromise: Promise<void> | undefined;
  let cronId: string | undefined;
  let worker: Awaited<ReturnType<typeof hatchet.worker>> | undefined;

  try {
    worker = await hatchet.worker(`heartbeat-ts-worker-${runId}`, {
      workflows: [heartbeatTask],
      slots: 10,
    });

    workerPromise = worker.start();

    const cron = await heartbeatTask.cron(cronName, "* * * * *", {});
    cronId = cron.metadata.id;

    await sleep(75_000);
  } finally {
    if (worker && workerPromise) {
      await worker.stop();
      await workerPromise;
    }

    if (cronId) {
      await hatchet.crons.delete(cronId);
    }
  }
};

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
