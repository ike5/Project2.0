# Module 05 — The subscriber / observer pattern

**Python skill:** storing a list of callables and calling them on every event. Closely related to Module 04.
**LeetCode problem:** [362. Design Hit Counter](https://leetcode.com/problems/design-hit-counter/) · Medium.
**Time:** ~1.5 h.

---

## 1. The pattern

An **observer** (or **subscriber**) pattern has two roles:

- The **subject** (or **publisher**) keeps a list of subscribers and calls them on each event.
- A **subscriber** is just a callable — `print`, a counter function, anything with one argument.

```python
class Newsfeed:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[str], None]] = []
        self._headlines: list[str] = []

    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._subscribers.append(fn)

    def unsubscribe(self, fn: Callable[[str], None]) -> None:
        self._subscribers.remove(fn)

    def add_headline(self, text: str) -> None:
        self._headlines.append(text)
        for fn in self._subscribers:
            fn(text)
```

That's it. The subject doesn't know or care what subscribers do; it just calls them.

## 2. Why this is a Pythonic pattern

In a strict OO language, the Observer pattern usually means defining a `Subscriber` interface and creating classes. In Python, *anything callable* is a subscriber:

```python
feed = Newsfeed()
feed.subscribe(print)                        # builtin
feed.subscribe(lambda h: print(f"  >> {h}"))  # lambda
feed.subscribe(my_logger.warning)            # bound method
```

This is the same "functions are first-class" idea as Strategy, just with a *list* of callables instead of one. The shape is the same: `self._subscribers: list[Callable]`.

## 3. The LeetCode problem

> [362. Design Hit Counter](https://leetcode.com/problems/design-hit-counter/)
>
> Design a hit counter which counts the number of hits received in the past 5 minutes (i.e., the past 300 seconds).
>
> - `hit(timestamp)` — record a hit at `timestamp` (in seconds).
> - `getHits(timestamp)` — return the number of hits in `[timestamp - 299, timestamp]`.

There are two flavors of this problem: one that assumes timestamps are non-decreasing and a queue of 300 buckets works, and one (the original) that uses a fixed-size `deque` and dequeues old entries.

For the original, the cleanest solution is a `collections.deque`:

```python
from collections import deque

class HitCounter:
    def __init__(self) -> None:
        self.queue: deque[int] = deque()

    def hit(self, timestamp: int) -> None:
        self.queue.append(timestamp)

    def getHits(self, timestamp: int) -> int:
        while self.queue and self.queue[0] <= timestamp - 300:
            self.queue.popleft()
        return len(self.queue)
```

This isn't really an "Observer" problem in the strict sense — but the *pattern* is there. The `HitCounter` "observes" each `hit` event and stores a log. `getHits` is the query. Notice the parallel to `RecentCounter` from Module 03's challenge: same shape, different time window.

## 4. The `Observer` framing

If you want to *see* the observer pattern, imagine:

```python
class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable]] = {}

    def on(self, event: str, fn: Callable) -> None:
        self._subs.setdefault(event, []).append(fn)

    def emit(self, event: str, *args) -> None:
        for fn in self._subs.get(event, []):
            fn(*args)
```

This is the shape behind GUI frameworks, logging libraries, and async event loops. We won't use it on LeetCode, but recognizing the shape will help you read real code.

## 5. Anti-patterns

- **Storing subscribers in a `set`.** Lists preserve order, and you can have duplicate subscribers.
- **Calling subscribers inside a `try/except` that swallows errors.** Decide whether one bad subscriber should break the others (usually it shouldn't).
- **Forgetting to clean up.** If subscribers hold references to other things, they prevent garbage collection. (We won't hit this in LeetCode problems, but it's a real production issue.)

---

**→ Next: [Module 06 — The wrapper / decorator pattern](./../06-decorator-pattern/)**
