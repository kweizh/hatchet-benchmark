import asyncio
import runner
async def main():
    ref = await runner.process_payment.aio_run({"user_id": "A"}, wait_for_result=False)
    print(dir(ref))
asyncio.run(main())
