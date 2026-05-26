from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()

@hatchet.task(name="test_task", on_events=["test:event"])
def test_task(context):
    pass

print("Task object:", test_task)
print("Dir:", dir(test_task))
