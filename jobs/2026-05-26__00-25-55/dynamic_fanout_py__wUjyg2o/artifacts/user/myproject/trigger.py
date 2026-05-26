import asyncio
import json
import sys
from workflows import process_batch

async def main():
    print("Triggering parent workflow 'process_batch' with items [1, 2, 3, 4, 5]...")
    try:
        # aio_run triggers and waits for result
        result = await process_batch.aio_run(input={"items": [1, 2, 3, 4, 5]})
        
        print(f"Workflow completed. Result: {result}")
        
        # Write result to /tmp/result.json
        output_path = "/tmp/result.json"
        with open(output_path, "w") as f:
            json.dump(result, f)
        
        print(f"Final output written to {output_path}")
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
