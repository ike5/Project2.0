# Python OOP & DSA Cheatsheet

A one-page reference for the Python you'll use on LeetCode. Print it, pin it, do what you want with it.

---

## Containers

```python
# list — ordered, mutable
xs = [1, 2, 3]
xs.append(4)           # O(1)
xs.pop()               # O(1) end
xs.pop(0)              # O(n) front  -> use collections.deque instead
xs[-1]                 # O(1) last
xs[1:4]                # O(k) slice, copies
xs.sort()              # in-place, O(n log n)
sorted(xs)             # new list, O(n log n)

# dict — hash map, O(1) average get/set
d = {"a": 1}
d["b"] = 2
d.get("c", 0)          # default if missing
"a" in d               # O(1) key check
for k, v in d.items():
    ...

# set — hash set, O(1) membership
s = {1, 2, 3}
s.add(4)
3 in s                 # O(1)

# tuple — immutable, hashable (can be a dict key)
t = (1, 2, 3)
d = {(1, 2): "pair"}   # OK
```

### Specialized containers

```python
from collections import Counter, defaultdict, OrderedDict, deque
import heapq

# Counter — counting
c = Counter("aabbc")              # {'a': 2, 'b': 2, 'c': 1}
c.most_common(2)                  # [('a', 2), ('b', 2)]

# defaultdict — default for missing keys
dd = defaultdict(list)
dd["x"].append(1)                 # no KeyError

# OrderedDict — remembers insertion order, supports move_to_end
od = OrderedDict()
od["a"] = 1
od.move_to_end("a")               # mark as recently used
od.popitem(last=True)             # evict LRU

# deque — O(1) on both ends
q = deque([1, 2, 3])
q.append(4)
q.appendleft(0)
q.pop()
q.popleft()

# heapq — min-heap on a list
heap = []
heapq.heappush(heap, 5)
heapq.heappop(heap)               # smallest
heapq.heapify([3, 1, 4, 1, 5])    # in-place
```

## Iteration patterns

```python
# for + enumerate (index + value)
for i, x in enumerate(xs):
    ...

# zip — pair multiple iterables
for a, b in zip(xs, ys):
    ...

# reversed — without copying
for x in reversed(xs):
    ...

# range — [start, stop) with optional step
for i in range(n):
for i in range(0, n, 2):

# while — when you don't know iteration count
left, right = 0, len(xs) - 1
while left < right:
    ...
```

## Comprehensions

```python
# list
[x * 2 for x in xs if x > 0]

# set
{x % 10 for x in xs}

# dict
{x: x * x for x in xs}

# generator (lazy)
sum(x * x for x in xs)
```

## Classes

```python
class ParkingSystem:
    def __init__(self, big: int, medium: int, small: int):
        self.slots = [big, medium, small]   # per-size capacity

    def addCar(self, carType: int) -> bool:
        if self.slots[carType - 1] == 0:
            return False
        self.slots[carType - 1] -= 1
        return True
```

### `@classmethod` and `@staticmethod`

```python
class C:
    n = 0

    @classmethod
    def from_string(cls, s):        # gets the class, not an instance
        return cls(int(s))

    @staticmethod
    def add(a, b):                  # just a function in the class namespace
        return a + b
```

### `@dataclass`

```python
from dataclasses import dataclass, field

@dataclass
class Tweet:
    id: int
    user_id: int
    ts: int
    text: str = ""           # default value
    likes: list[int] = field(default_factory=list)  # mutable default
```

## Magic methods

```python
class Stack:
    def __init__(self):
        self._data = []

    def __repr__(self):                   # repr(stack)
        return f"Stack({self._data!r})"

    def __len__(self):                    # len(stack)
        return len(self._data)

    def __getitem__(self, i):             # stack[0]
        return self._data[i]

    def __iter__(self):                   # for x in stack
        return iter(self._data)

    def __contains__(self, x):            # x in stack
        return x in self._data

    def __eq__(self, other):              # stack1 == stack2
        return isinstance(other, Stack) and self._data == other._data
```

> **Warning:** if you define `__eq__`, Python sets `__hash__ = None` and your object is no longer hashable. Override `__hash__` explicitly to keep it hashable.

## Design patterns — at a glance

| Pattern | One-liner | LeetCode example |
|---|---|---|
| **Strategy** | Pass a function/algorithm into `__init__` | A class that takes a comparison function |
| **Observer** | Subject keeps a list of subscribers | A hit counter with timestamp buckets |
| **Decorator** | Wrap an object to add behavior | LRU cache = `OrderedDict` + bounds check |
| **Factory** | `cls.from_X(...)` builds the right thing | Build a `LinkedList` from an array |
| **Adapter** | Translate one interface to another | `MinStack` wraps a list to track mins |
| **Composition** | Object holds other objects | `Twitter` holds a `deque` of tweets per user |

## DSA idioms — at a glance

| Idiom | When | Complexity |
|---|---|---|
| **Hash map** | Need O(1) lookup by value | O(n) time, O(n) space |
| **Two-pointer** | Sorted array, find pair | O(n) |
| **Sliding window** | Longest subarray with property | O(n) |
| **Binary search** | Sorted, "find boundary" | O(log n) |
| **BFS** | Shortest path in unweighted graph | O(V + E) |
| **DFS** | Explore / count connected components | O(V + E) |
| **Monotonic stack** | "Next greater element" | O(n) |
| **Heap** | Top-k / k-th smallest | O(n log k) |
| **Union-Find** | Connected components, dynamic connectivity | O(α(n)) per op |

## Time/space complexity cheat codes

- A single pass over `n` items: `O(n)`.
- Nested loops over `n`: usually `O(n²)`.
- `dict.get`, `set.add`, `list.append`: `O(1)`.
- `list.pop(0)`, `list.insert(0, x)`: `O(n)` — use `deque`.
- `x in list`: `O(n)`. `x in set`: `O(1)`.
- `sorted(xs)`: `O(n log n)` and allocates a new list.
