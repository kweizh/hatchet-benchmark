from hatchet_sdk import Hatchet
h = Hatchet()
@h.task()
def call_external_api(context):
    pass
print(dir(call_external_api))
