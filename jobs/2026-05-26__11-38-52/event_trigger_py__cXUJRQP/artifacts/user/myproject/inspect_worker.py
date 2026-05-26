from hatchet_sdk import Hatchet

hatchet = Hatchet()

@hatchet.task(name="on_user_created", on_events=["user:created"])
def on_user_created(context):
    pass

worker = hatchet.worker("test-worker", workflows=[on_user_created])
print("Worker created")
