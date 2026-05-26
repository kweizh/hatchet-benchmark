import os
from hatchet_sdk import Hatchet

hatchet = Hatchet()
worker = hatchet.worker("test")
print(dir(worker))
