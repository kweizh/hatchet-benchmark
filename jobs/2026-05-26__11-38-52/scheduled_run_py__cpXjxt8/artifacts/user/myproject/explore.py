import json
from datetime import datetime, timedelta, timezone
from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()

@hatchet.task(name="scheduled-hello")
def scheduled_hello(context):
    pass

print(dir(scheduled_hello))
print(dir(hatchet.admin))
