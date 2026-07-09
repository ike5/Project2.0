# Python Cheatsheet for NeetCode 150 🐍

Handy Python idioms you'll see in the solutions. All examples are
**Python 3.10+** (we use `match`, `int | str` union types, structural pattern
matching, etc.).

---

## Containers

| Need | Use | Why |
|------|-----|-----|
| `dict` with default 0 | `collections.Counter`, `defaultdict(int)` | Avoids `KeyError` |
| `dict` with default list | `defaultdict(list)` | Clean adjacency lists |
| `dict` with default set | `defaultdict(set)` | Clean visited sets |
| Sort by key | `sorted(items, key=lambda x: x[1])` | Common in intervals |
| Sort by tuple | `sorted(intervals, key=lambda x: (x[0], x[1]))` | Multi-key |
| Invert a dict | `{v: k for k, v in d.items()}` | O(n) |
| Group by key | `itertools.groupby(sorted(items, key=...))` | O(n log n) due to sort |
| Min by key | `min(items, key=...)` | O(n) |
| K smallest | `heapq.nsmallest(k, items)` | O(n log k) |
| K largest | `heapq.nlargest(k, items)` | O(n log k) |
| Flatten 2D | `[x for row in m for x in row]` | — |
| Transpose | `list(zip(*m))` | — |
| Rotate list | `nums[-k:] + nums[:-k]` | O(n) |
| Reverse in place | `nums.reverse()` or `nums[::-1]` | slice returns new list |

## `heapq` (min-heap by default)

```python
import heapq

heap = []              # a min-heap
heapq.heappush(heap, x)  # O(log n)
x = heapq.heappop(heap)  # O(log n)
x = heap[0]            # peek at the min, O(1)
# Max-heap trick: push -x
heapq.heappush(heap, -x)
x = -heapq.heappop(heap)
```

## `bisect` (binary search on a sorted list)

```python
import bisect
idx = bisect.bisect_left(a, x)   # leftmost index where x could be inserted
idx = bisect.bisect_right(a, x)  # rightmost index + 1
bisect.insort(a, x)              # insert keeping sorted order
```

## Strings

```python
s.split(sep)         # list of parts
sep.join(parts)      # join into one string
s[i:j]               # slice (new string)
s.strip()            # whitespace
s.isalnum()          # letters or digits
ord(c), chr(n)       # char↔codepoint
```

## `collections`

```python
from collections import Counter, defaultdict, deque

cnt = Counter("aabbc")  # Counter({'a': 2, 'b': 2, 'c': 1})
cnt.most_common(k)      # top-k items
d = defaultdict(list)
d["x"].append(1)        # no KeyError
q = deque()             # O(1) append, popleft, appendleft, pop
```

## `itertools`

```python
from itertools import permutations, combinations, product, accumulate

list(permutations([1, 2, 3]))                  # 6 perms
list(combinations([1, 2, 3], 2))               # C(3,2) = 3
list(product([1, 2], repeat=2))                # 4 pairs
list(accumulate([1, 2, 3, 4]))                  # [1, 3, 6, 10] (running sum)
```

## `math`

```python
import math
math.inf, -math.inf
math.gcd(a, b)
math.isqrt(n)         # integer sqrt
math.log2(n)          # log base 2
```

## `dataclass`

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Node:
    val: int
    next: Optional["Node"] = None
    neighbors: list["Node"] = field(default_factory=list)
```

## `functools`

```python
from functools import lru_cache, cmp_to_key

@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)
```

## Bit manipulation

```python
x & y, x | y, x ^ y, ~x
x << k, x >> k
x & -x                 # lowest set bit
x & (x - 1)            # clear the lowest set bit
x.bit_count()          # number of set bits (Py 3.10+)
x.bit_length()         # bits needed to represent x
```

## Type hints we use

```python
from typing import Optional, List, Tuple, Dict, Set, Deque
from collections import deque
```

## Common patterns

**Adjacency list for a tree/graph:**
```python
graph: Dict[int, List[int]] = defaultdict(list)
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)
```

**BFS level-order:**
```python
q = deque([(start, 0)])
while q:
    node, dist = q.popleft()
    for nei in graph[node]:
        if nei not in visited:
            visited.add(nei)
            q.append((nei, dist + 1))
```

**DFS recursive:**
```python
def dfs(node, parent):
    for nei in graph[node]:
        if nei != parent:
            dfs(nei, node)
```

**Two pointers opposite ends:**
```python
l, r = 0, len(nums) - 1
while l < r:
    s = nums[l] + nums[r]
    if s == target: return [l, r]
    if s < target: l += 1
    else:          r -= 1
```

**Sliding window:**
```python
l = 0
for r in range(len(s)):
    # add s[r] to window
    while invalid():
        # remove s[l] from window
        l += 1
    # update answer
```

**Binary search on answer:**
```python
lo, hi = MIN, MAX
while lo < hi:
    mid = (lo + hi) // 2
    if feasible(mid):
        hi = mid
    else:
        lo = mid + 1
return lo
```

## Python pitfalls to avoid

- **`dict` ordering is insertion order in 3.7+**, but never rely on
  alphabetical key order.
- **`for i in range(len(a))` then `a[i]`** → prefer `enumerate(a)`.
- **`list` is not a hashable type.** You can't put lists in a `set` or as
  `dict` keys. Use `tuple` instead.
- **`s.sort()` returns `None` and mutates.** `sorted(s)` returns a new list.
- **`a = a + b` vs `a += b`** — for `list` they're equivalent; for
  immutable types like `tuple` they behave the same; for `__iadd__`-overriding
  classes they may differ.
- **Recursion limit** is 1000 by default. For deep recursion, use iterative
  DFS or `sys.setrecursionlimit(10**6)`.
