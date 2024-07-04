from collections import defaultdict
from textual.cache import LRUCache

colorCaches = defaultdict[int, LRUCache[int, str]](lambda: LRUCache(512)) # no one have more than 200 servers joined so we dont have to care about lrucacing the dict itself
"format: {'serverId': {'userId': 'displayColor (hex)'}}"

