"""pytest tests for LRU Cache."""

from lru_cache import LRUCache


def test_leetcode_example():
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)
    assert cache.get(2) == -1            # evicted
    cache.put(4, 4)
    assert cache.get(1) == -1            # evicted
    assert cache.get(3) == 3
    assert cache.get(4) == 4


def test_update_does_not_evict():
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(1, 10)                     # update, not a new key
    assert cache.get(1) == 10
    assert cache.get(2) == 2             # still there


def test_capacity_one():
    cache = LRUCache(1)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == -1
    assert cache.get(2) == 2
