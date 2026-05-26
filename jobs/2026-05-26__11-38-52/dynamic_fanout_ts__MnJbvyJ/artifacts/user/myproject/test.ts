import { Hatchet } from '@hatchet-dev/typescript-sdk';
const hatchet = Hatchet.init();
async function main() {
  const worker = await hatchet.worker('test');
  console.log(Object.getOwnPropertyNames(Object.getPrototypeOf(worker)));
}
main();
