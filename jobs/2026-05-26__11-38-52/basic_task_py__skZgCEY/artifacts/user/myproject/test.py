import os
from hatchet_sdk import Hatchet

hatchet = Hatchet()

@hatchet.task()
def simple_greeting(context):
    pass

print(dir(simple_greeting))
