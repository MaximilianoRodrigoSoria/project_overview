import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.adapters.cache_memory import MemoryCache


def test_cache_memory_respects_ttl():
    cache = MemoryCache()
    cache.set("key", "value", ttl_seconds=1)
    assert cache.get("key") == "value"
    time.sleep(1.1)
    assert cache.get("key") is None
