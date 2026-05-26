import fs from "node:fs";
import { workflow } from "./workflow.js";

const result = await workflow.run({});

const finalOutput = result.step3;

fs.writeFileSync("/tmp/result.json", JSON.stringify(finalOutput));
