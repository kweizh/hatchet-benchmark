from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()
print(hasattr(hatchet, 'admin'))
if hasattr(hatchet, 'admin'):
    print(inspect.signature(hatchet.admin.run_workflow))
