import os
import time
from hatchet_sdk import Hatchet
hatchet = Hatchet()
@hatchet.task(name="heartbeat")
def heartbeat(context):
    print("Heartbeat task executed")
print("Task defined")
