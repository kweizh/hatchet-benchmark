from hatchet_sdk import Hatchet
import inspect

hatchet = Hatchet()
print(dir(hatchet))
if hasattr(hatchet, 'client'):
    print("client dir:", dir(hatchet.client))
    if hasattr(hatchet.client, 'event'):
        print("client.event dir:", dir(hatchet.client.event))
    if hasattr(hatchet.client, 'admin'):
        print("client.admin dir:", dir(hatchet.client.admin))
if hasattr(hatchet, 'event'):
    print("event dir:", dir(hatchet.event))
