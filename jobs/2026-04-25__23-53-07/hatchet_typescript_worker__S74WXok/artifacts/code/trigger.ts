import Hatchet from '@hatchet-dev/typescript-sdk';

const hatchet = Hatchet.init();

async function main() {
  await hatchet.event.push('user:create', {
    username: 'Alice',
  });
  console.log('Event user:create pushed with username Alice');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
