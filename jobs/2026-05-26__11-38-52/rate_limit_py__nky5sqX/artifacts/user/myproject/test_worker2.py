from hatchet_sdk import Hatchet
h = Hatchet()
@h.task()
def call_external_api(context):
    pass
w = h.worker("rate-limit-worker", slots=20, workflows=[call_external_api])
print("Worker created successfully!")
