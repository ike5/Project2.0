# Module 06 — The wrapper / decorator pattern

**Python skill:** wrapping an object to add behavior without changing the original. `OrderedDict` and `move_to_end`.
**LeetCode problem:** [146. LRU Cache](https://leetcode.com/problems/lru-cache/) · Medium.
**Time:** ~2 h.

---

## 1. The pattern

The Decorator pattern says: take an object, wrap it in another object that adds behavior, and the wrapper presents the *same interface* (so callers can't tell the difference). It's the OOP version of function decorators, but applied to objects.

```python
class Logger:
    def log(self, msg: str) -> None:
        print(msg)


class UpperLogger:
    def __init__(self, inner: Logger) -> None:
        self.inner = inner

    def log(self, msg: str) -> None:
        self.inner.log(msg.upper())


class TimestampedLogger:
    def __init__(self, inner: Logger) -> None:
        self.inner = inner

    def log(self, msg: str) -> None:
        from datetime import datetime
        self.inner.log(f"[{datetime.now():%H:%M:%S}] {msg}")


# Compose them: each layer wraps the one below.
log = TimestampedLogger(UpperLogger(Logger()))
log.log("hi")     # [HH:MM:SS] HI
```

The same `.log(msg)` interface, the same call, but each wrapper added one piece of behavior. You can stack as many as you like.

## 2. Why this matters for LeetCode

The most famous LeetCode problem in this style is **LRU Cache** (LeetCode 146). An LRU cache is a key-value store that:

- Supports `get(key)` and `put(key, value)` in O(1).
- Evicts the *least recently used* key when the cache is full and you insert a new one.
- Updates "recency" on every `get` and `put`.

The cleanest Python implementation wraps `OrderedDict` — a `dict` that remembers insertion order and supports `move_to_end`:

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)        # mark as recently used
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False) # evict LRU (the first item)
```

The `OrderedDict` is the inner object. Our `LRUCache` *wraps* it, exposing a different interface (capacity-bounded) and adding behavior (eviction on overflow). That's the decorator pattern in action.

## 3. `OrderedDict` vs plain `dict`

Since Python 3.7, `dict` *does* remember insertion order. So why `OrderedDict`?

- **`OrderedDict.move_to_end(key)`** is the killer feature. There's no equivalent on `dict`.
- **`OrderedDict.popitem(last=False)`** pops the *oldest* item — also missing from `dict`.

If you only need order and don't need to mutate recency, plain `dict` is fine. For LRU/LFU caches, `OrderedDict` is the right tool.

## 4. The LeetCode problem

> [146. LRU Cache](https://leetcode.com/problems/lru-cache/)
>
> Design a data structure that follows the constraints of a **least recently used (LRU) cache**.
>
> Implement the `LRUCache` class:
>
> - `LRUCache(int capacity)` — initialize with positive capacity.
> - `int get(int key)` — return the value if the key exists, otherwise `-1`.
> - `void put(int key, int value)` — insert / update. If the number of keys exceeds `capacity`, evict the least recently used key.
>
> The functions `get` and `put` must each run in **O(1)** average time.

The implementation in section 2 is the entire solution. You'll build it in the lab.

## 5. Anti-patterns

- **Implementing LRU on top of plain `list`.** `list.remove(x)` is O(n) — you'll TLE on `n = 10⁵`. Use `OrderedDict`.
- **Calling `sorted` on the dict on every operation.** That defeats O(1). `move_to_end` is O(1).
- **Storing a separate `(value, prev, next)` linked list manually.** It works but is verbose. `OrderedDict` is the idiomatic Python answer.

---

**→ Next: [Module 07 — The factory pattern](./../07-factory-pattern/)**
