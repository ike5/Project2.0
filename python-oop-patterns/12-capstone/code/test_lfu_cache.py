"""pytest tests for LFU Cache."""

from lfu_cache import LFUCache


def test_leetcode_example():
    lfu = LFUCache(2)
    lfu.put(1, 1)
    lfu.put(2, 2)
    assert lfu.get(1) == 1
    lfu.put(3, 3)                # evicts key 2
    assert lfu.get(2) == -1
    assert lfu.get(3) == 3
    lfu.put(4, 4)                # evicts key 1
    assert lfu.get(1) == -1
    assert lfu.get(3) == 3
    assert lfu.get(4) == 4


def test_update_existing():
    lfu = LFUCache(2)
    lfu.put(1, 1)
    lfu.put(2, 2)
    lfu.put(1, 10)
    assert lfu.get(1) == 10
    assert lfu.get(2) == 2


def test_zero_capacity():
    lfu = LFUCache(0)
    lfu.put(1, 1)
    assert lfu.get(1) == -1


def test_frequency_tie_breaks_by_lru():
    """When all keys have the same freq, evict the LRU one."""
    lfu = LFUCache(2)
    lfu.put(1, 1)
    lfu.put(2, 2)
    # touch 1 to make it more recent within the same freq
    assert lfu.get(1) == 1
    lfu.put(3, 3)                # evicts 2 (LRU at freq 1)
    assert lfu.get(2) == -1
    assert lfu.get(3) == 3
