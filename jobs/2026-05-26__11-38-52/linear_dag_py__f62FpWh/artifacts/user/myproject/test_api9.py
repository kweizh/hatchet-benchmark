from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()
workflow = hatchet.workflow(name="test")
print(hasattr(workflow, 'run'))
if hasattr(workflow, 'run'):
    print(inspect.signature(workflow.run))
