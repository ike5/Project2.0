# Module 12 — Capstone: design an LFU cache

**Python skill:** every pattern from Modules 01–11 — `dict` as a hash map, `OrderedDict` for O(1) recency, composition, decorators, strategy, dataclasses.
**LeetCode problem:** [460. LFU Cache](https://leetcode.com/problems/lfu-cache/) · Hard.
**Time:** ~2 h.

---

## 1. LFU vs LRU — the difference

- **LRU (Module 06)**: evict the *least recently used* item.
- **LFU (this module)**: evict the *least frequently used* item; break ties by oldest.

Both need O(1) `get` and `put`. LRU does it with one `OrderedDict`. LFU needs three things:

1. `vals[k]` — the value of key `k`.
2. `counts[k]` — the frequency of key `k`.
3. `buckets[f]` — an `OrderedDict` of keys that have frequency `f`. The order in this `OrderedDict` is *recency* (most recent at the end).
4. `min_freq` — the smallest non-empty frequency. The eviction target is `buckets[min_freq]`'s first item.

On `get(k)`, the key's frequency goes up by 1, and the key moves to `buckets[f + 1]`'s end. On `put`, same plus eviction if over capacity.

The invariants are subtle. Trace through the LeetCode example carefully.

## 2. The implementation

```python
from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.vals: dict[int, int] = {}
        self.counts: dict[int, int] = {}
        self.buckets: dict[int, "OrderedDict[int, None]"] = defaultdict(OrderedDict)
        self.min_freq = 0

    def _bump(self, key: int) -> None:
        """Move key from its current frequency bucket to freq+1."""
        f = self.counts[key]
        del self.buckets[f][key]
        if not self.buckets[f] and self.min_freq == f:
            self.min_freq += 1
        self.counts[key] = f + 1
        self.buckets[f + 1][key] = None

    def get(self, key: int) -> int:
        if key not in self.vals:
            return -1
        self._bump(key)
        return self.vals[key]

    def put(self, key: int, value: int) -> None:
        if self.cap == 0:
            return
        if key in self.vals:
            self.vals[key] = value
            self._bump(key)
            return
        if len(self.vals) >= self.cap:
            # Evict LRU within the lowest-frequency bucket.
            evict_key, _ = self.buckets[self.min_freq].popitem(last=False)
            del self.vals[evict_key]
            del self.counts[evict_key]
        self.vals[key] = value
        self.counts[key] = 1
        self.buckets[1][key] = None
        self.min_freq = 1
```

Every pattern from the course shows up here:

- **Dict as hash map** (Module 01) — `vals`, `counts` are O(1) lookups.
- **Loops / iteration** (Module 02) — none visible, but `popitem` does internal iteration.
- **Classes & self** (Module 03) — `LFUCache` is a class with state.
- **Strategy** (Module 04) — you could parameterize the eviction policy.
- **OrderedDict.move_to_end / popitem** (Module 06) — the eviction logic.
- **defaultdict** (Module 01) — `buckets` is a `defaultdict(OrderedDict)`.
- **Composition** (Module 11) — `LFUCache` *holds* three dicts and an int.

## 3. Tracing the LeetCode 460 example

```
LFUCache(2)
put(1,1)         vals={1:1}, counts={1:1}, buckets[1]={1:None}, min_freq=1
put(2,2)         vals={1:1,2:2}, counts={1:1,2:1}, buckets[1]={1,2}, min_freq=1
get(1)           bump(1): counts[1]=2, buckets[1]={2}, buckets[2]={1}, min_freq=1
                 (still 1 because buckets[1] is non-empty)
put(3,3)         vals full; evict LRU in buckets[1] = key 2
                 vals={1:1,3:3}, counts={1:2,3:1}, buckets[1]={3}, buckets[2]={1}, min_freq=1
get(2)           not in vals -> -1
get(3)           bump(3): counts[3]=2, buckets[1]={}, min_freq=2, buckets[2]={1,3}
                 return 3
put(4,4)         vals full; evict LRU in buckets[2] = key 1
                 vals={3:3,4:4}, counts={3:2,4:1}, buckets[1]={4}, buckets[2]={3}, min_freq=1
get(1)           -1
get(3)           bump(3): counts[3]=3, buckets[1]={4}, buckets[2]={}, min_freq=2
                 buckets[3]={3}
                 return 3
get(4)           bump(4): counts[4]=2, buckets[1]={}, min_freq=2
                 buckets[2]={3,4}
                 return 4
```

## 4. Submission

Submit your implementation to [460. LFU Cache](https://leetcode.com/problems/lfu-cache/). It will accept O(1) average-time solutions.

---

**→ End of course.** You can now write Python classes that wrap Python containers in the right way for hard LeetCode design problems. Go solve more.
