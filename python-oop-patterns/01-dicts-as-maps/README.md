# Module 01 — Dicts as hash maps

**Python skill:** `dict` as an O(1) hash map — the single most useful data structure in LeetCode. Get/set, `get` with default, `Counter`, `defaultdict`, dict as a visited set.
**LeetCode problem:** [1. Two Sum](https://leetcode.com/problems/two-sum/) · Easy.
**Time:** ~1.5 h.

---

## 1. Why this lesson first

Most "easy" LeetCode problems become "medium" the moment you stop using nested loops. The fix is almost always a `dict` doing O(1) lookups instead of an `O(n²)` "for every pair, check" loop.

`dict` in Python is a *hash map*: a structure that maps hashable keys to values with O(1) average-time get/set/delete. Anything that involves "have I seen this before?" or "what index did I last see this value at?" wants a `dict`.

## 2. The five dict operations you must know

```python
d = {}                    # empty dict
d[key] = value            # set (O(1) average)
value = d[key]            # get, raises KeyError if missing
value = d.get(key, default)  # get, returns default if missing
key in d                  # membership test (O(1))
```

Two more you'll use constantly:

```python
d.pop(key)                # remove and return
d.pop(key, default)       # pop, return default if missing
```

And three high-level ones from `collections`:

```python
from collections import Counter, defaultdict

c = Counter(iterable)                # count occurrences
dd = defaultdict(list)                # missing keys -> empty list
dd[key].append(value)                 # no KeyError, no check needed
```

## 3. The brute force vs. the hash map

A classic interview warm-up: given a list of numbers, find two that add up to a target.

**Brute force (O(n²) time, O(1) extra space):**

```python
def two_sum_brute(nums, target):
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
```

**Hash map (O(n) time, O(n) extra space):**

```python
def two_sum(nums, target):
    seen = {}                          # value -> index
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return [seen[need], i]
        seen[x] = i
    return []
```

The hash map version is *one* pass, not two. For `n = 10⁴` that's `10⁸` operations vs `10⁴`. Huge difference.

## 4. Counter and defaultdict

When you're counting things — characters in a string, occurrences of an element, frequencies in a list — `Counter` is your friend:

```python
from collections import Counter

c = Counter("abracadabra")
# c == {'a': 5, 'b': 2, 'r': 2, 'c': 1, 'd': 1}
c.most_common(2)        # [('a', 5), ('b', 2)]
```

When you're *grouping* things by some key, `defaultdict(list)` is the right tool:

```python
from collections import defaultdict

groups = defaultdict(list)
for word in words:
    groups[len(word)].append(word)

groups[3]   # all 3-letter words
```

The alternative is `groups.setdefault(key, []).append(value)`, which is fine but uglier. `defaultdict` makes the intent obvious.

## 5. Dict as a visited set

Sometimes you don't need a value at all — just "have I seen this before?". A `set` does that in `O(1)`:

```python
seen = set()
for ch in s:
    if ch in seen:
        ...               # duplicate
    seen.add(ch)
```

A `dict` does the same thing if you ever need to store something with the key (e.g. the *index* of the last occurrence, like in `two_sum` above). When in doubt: if you only need membership, use a `set`; if you need a value, use a `dict`.

## 6. The LeetCode problem

Open [1. Two Sum](https://leetcode.com/problems/two-sum/). Read the prompt.

> Given an array of integers `nums` and an integer `target`, return *indices of the two numbers such that they add up to `target`*. You may assume that each input would have **exactly one solution**, and you may not use the same element twice. You can return the answer in any order.

You should be able to write a one-pass dict solution in under five minutes after this lesson. In the lab, you'll build it step by step. In the challenge, you'll implement `two_sum` and test it with `pytest`.

## 7. Anti-patterns to watch for

- **`x in list`** is O(n). If you find yourself writing it inside a loop, replace the list with a `set`.
- **`list.index(x)`** is O(n) too. If you call it inside a loop, build a `{value: index}` dict first.
- **Nested `for` loops over the same data** are usually a sign that a hash map would do.

---

**→ Next: [Module 02 — Loops & iteration patterns](./../02-loops-and-iteration/)**
