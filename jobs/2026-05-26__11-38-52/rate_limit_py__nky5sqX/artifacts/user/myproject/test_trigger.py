import multiprocessing
from hatchet_sdk import Hatchet
h = Hatchet()
@h.task()
def call_external_api(context):
    pass
print("Triggering...")
call_external_api.run({}, wait_for_result=False)
print("Done")
