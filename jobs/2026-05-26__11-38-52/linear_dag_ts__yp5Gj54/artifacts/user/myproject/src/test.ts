import { Hatchet } from '@hatchet-dev/typescript-sdk';

const hatchet = Hatchet.init();
const workflow = hatchet.workflow('test', 'test');
console.log(Object.keys(workflow));
