import { Hatchet } from '@hatchet-dev/typescript-sdk';
const hatchet = new Hatchet();
const wf = hatchet.workflow({ name: 'test-wf', on: { event: 'test:run' } });
console.log(Object.keys(wf));
console.log(typeof wf.task);
