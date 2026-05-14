import Hatchet, { Workflow } from '@hatchet-dev/typescript-sdk';
import * as fs from 'fs';
import * as path from 'path';

const hatchet = Hatchet.init();

const workflow: Workflow = {
  id: 'user-create-workflow',
  description: 'Greet the user',
  on: {
    event: 'user:create',
  },
  steps: [
    {
      name: 'greet',
      run: async (ctx) => {
        const input = ctx.workflowInput();
        const username = input.username;
        const result = { message: `Welcome ${username}` };
        
        const logPath = '/home/user/app/output.log';
        fs.writeFileSync(logPath, JSON.stringify(result));
        
        return result;
      },
    },
  ],
};

async function main() {
  const worker = await hatchet.worker('test-worker');
  await worker.registerWorkflow(workflow);
  worker.start();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
