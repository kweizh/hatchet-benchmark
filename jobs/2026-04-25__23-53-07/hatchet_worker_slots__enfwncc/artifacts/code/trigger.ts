import { Hatchet } from '@hatchet-dev/typescript-sdk';
import { spawn } from 'child_process';

const hatchet = Hatchet.init();

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  console.log('Starting worker in background...');
  const workerProcess = spawn('npx', ['ts-node', '--esm', 'worker.ts'], {
    stdio: 'inherit',
    env: process.env,
  });

  // Give the worker some time to register and start
  await sleep(10000);

  console.log('\n--- Scenario 1: Standard Sleep (Blocking) ---');
  console.log('Triggering StandardSleepTask...');
  await hatchet.event.push('standard:sleep', {});
  await sleep(1000); // Small gap
  console.log('Triggering TestTask (should be blocked)...');
  await hatchet.event.push('test:task', {});

  // Wait for Scenario 1 to complete (Standard sleep 5s + TestTask)
  await sleep(15000);

  console.log('\n--- Scenario 2: Durable Sleep (Non-blocking) ---');
  console.log('Triggering DurableSleepTask...');
  await hatchet.event.push('durable:sleep', {});
  await sleep(1000); // Small gap
  console.log('Triggering TestTask (should execute immediately)...');
  await hatchet.event.push('test:task', {});

  // Wait for Scenario 2 to complete
  await sleep(15000);

  console.log('\nDemonstration complete. Killing worker...');
  workerProcess.kill();
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
