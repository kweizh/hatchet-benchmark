from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()
print(inspect.signature(hatchet.task))
