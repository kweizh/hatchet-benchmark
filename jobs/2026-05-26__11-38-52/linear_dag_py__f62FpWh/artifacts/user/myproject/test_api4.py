from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()
workflow = hatchet.workflow(name="test")
print(hasattr(workflow, 'task'))
if hasattr(workflow, 'task'):
    print(inspect.signature(workflow.task))
