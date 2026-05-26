import os
import json
import time
from datetime import datetime, timedelta, timezone
from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()

@hatchet.task(name="scheduled-hello")
def scheduled_hello(context):
    print("Inside task")

print("Task defined successfully")
