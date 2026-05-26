from hatchet_sdk import Hatchet
import inspect
h = Hatchet()
print(inspect.signature(h.rate_limits.put))
