from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()
worker = hatchet.worker("test")
print(inspect.signature(hatchet.worker))
