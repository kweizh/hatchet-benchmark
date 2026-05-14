import json
import os
from hatchet_sdk import Hatchet

# Initialize the Hatchet client
# HATCHET_CLIENT_TOKEN should be in the environment
hatchet = Hatchet()

@hatchet.workflow(on_crons=["* * * * *"])
class BatchProcessor:
    @hatchet.step()
    def process_records(self, context):
        records_path = "/home/user/app/records.json"
        log_path = "/home/user/app/output.log"
        
        try:
            if not os.path.exists(records_path):
                return {"error": "records.json not found"}
                
            with open(records_path, "r") as f:
                records = json.load(f)
                
            count = len(records)
            
            # Append a line to the log file
            with open(log_path, "a") as f:
                f.write(f"Processed {count} records\n")
                
            return {"processed": count}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Start the Hatchet worker
    worker = hatchet.worker("batch-worker")
    worker.register_workflow(BatchProcessor())
    worker.start()
