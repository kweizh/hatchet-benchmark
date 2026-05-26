import fs from 'fs';
import { workflow } from './workflow.js';

async function main() {
  const res = await workflow.run({});
  
  // The result has keys for each task
  const finalOutput = res.step3;
  
  fs.writeFileSync('/tmp/result.json', JSON.stringify(finalOutput, null, 2));
  console.log('Result written to /tmp/result.json');
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
