import fs from "fs";
import { workflow } from "./workflow.js";

async function main() {
  const result = await workflow.run({});

  const step3Output = result.step3;

  console.log("Workflow completed. step3 output:", step3Output);

  fs.writeFileSync("/tmp/result.json", JSON.stringify(step3Output));

  console.log("Result written to /tmp/result.json");
}

main().catch((err) => {
  console.error("Runner error:", err);
  process.exit(1);
});
