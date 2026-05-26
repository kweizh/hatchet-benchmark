import { Hatchet } from '@hatchet-dev/typescript-sdk';
const hatchet = new Hatchet();
const wf = hatchet.workflow({ name: 'test-wf', on: { event: 'test:run' } });
const t = wf.task({ name: 'step1', fn: async (ctx) => { return { text: 'hi' }; } });
console.log(t);
