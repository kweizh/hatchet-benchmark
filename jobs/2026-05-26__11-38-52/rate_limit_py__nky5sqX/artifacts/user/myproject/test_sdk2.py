from hatchet_sdk import Hatchet
h = Hatchet()
print(dir(h._client))
if hasattr(h._client, 'admin'):
    print(dir(h._client.admin))
