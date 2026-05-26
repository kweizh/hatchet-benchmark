from hatchet_sdk import Hatchet
import inspect

h = Hatchet()
@h.task()
def call_external_api(context):
    pass

print(inspect.signature(call_external_api.run))
