import { workflow } from "./workflow.js";
import * as fs from "fs";

async function main() {
  const run = await workflow.run({});
  const result = await run.result();
  
  console.log("DAG Result:", JSON.stringify(result, null, 2));
  
  const step3Output = result.step3 || result;
  
  fs.writeFileSync("/tmp/result.json", JSON.stringify(step3Output, null, 2));
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
