from hatchet_sdk import Hatchet
import inspect

h = Hatchet()
print(dir(h))
if hasattr(h, 'admin'):
    print(dir(h.admin))
if hasattr(h, 'client'):
    print(dir(h.client))
    if hasattr(h.client, 'admin'):
        print(dir(h.client.admin))
