import fs from 'fs';
import { workflow } from './workflow';

async function main() {
  console.log('Triggering workflow...');
  const result: any = await workflow.run({});
  
  // The DAG run result is keyed by task name
  const step3Output = result.step3;
  
  console.log('Final output:', step3Output);
  
  fs.writeFileSync('/tmp/result.json', JSON.stringify(step3Output));
  console.log('Result written to /tmp/result.json');
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
