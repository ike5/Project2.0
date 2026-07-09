# Module 05 — Binary Search 🎯

**Goal:** halve the search space every step. ⏱️ ~4 h · 🎯 Prereq: 04.

```
binary search: O(log n) by maintaining a monotone invariant
```

---

## 1. When does binary search apply?

A problem is a binary-search problem if the answer space has a **monotone
predicate**: a function `f(x)` that goes from `True` to `False` (or vice
versa) and stays there. Once you can spot a monotone predicate, you can
search the boundary in O(log n).

Two flavors:

- **Index search** — search the *position* of a target in a sorted array.
- **Search on answer** — search the *value* of an answer that satisfies
  the predicate (Koko, Median, Allocate Books, etc.).

## 2. The two templates

### Find exact match

```python
lo, hi = 0, n - 1
while lo <= hi:
    mid = lo + (hi - lo) // 2
    if arr[mid] == target: return mid
    if arr[mid] < target: lo = mid + 1
    else:                 hi = mid - 1
return -1
```

### Find first `True` in a boolean array

```python
lo, hi = 0, n        # hi is exclusive
while lo < hi:
    mid = lo + (hi - lo) // 2
    if f(mid): hi = mid
    else:      lo = mid + 1
return lo             # first True, or n if no True
```

This second template handles *search on answer* problems.

## 3. The 7 problems — easy → hard

| #  | Problem | Difficulty | Flavor |
|----|---------|-----------|--------|
| 01 | [Binary Search](./problems/01-binary-search/) | Easy | Exact match |
| 02 | [Search a 2D Matrix](./problems/02-search-a-2d-matrix/) | Medium | Exact match, flat-indexed |
| 03 | [Koko Eating Bananas](./problems/03-koko-eating-bananas/) | Medium | Search on answer |
| 04 | [Find Min in Rotated Sorted Array](./problems/04-find-minimum-in-rotated-sorted-array/) | Medium | Find pivot |
| 05 | [Search in Rotated Sorted Array](./problems/05-search-in-rotated-sorted-array/) | Medium | Find pivot, then check which half |
| 06 | [Time Based Key-Value Store](./problems/06-time-based-key-value-store/) | Medium | Per-key binary search |
| 07 | [Median of Two Sorted Arrays](./problems/07-median-of-two-sorted-arrays/) | Hard | Partition with binary search |

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Integer division | `lo + (hi - lo) // 2` | `lo + (hi - lo) / 2` |
| Negative infinity | `float('-inf')` | `Integer.MIN_VALUE` |
| Positive infinity | `float('inf')` | `Integer.MAX_VALUE` |
| `bisect` module | `bisect_left`, `bisect_right` | `Arrays.binarySearch` |
| Float division | `a / b` returns float | `(double) a / b` |

> **Watch out for `int` overflow in Java.** `(lo + hi) / 2` can overflow
> when both are near `Integer.MAX_VALUE`. Use `lo + (hi - lo) / 2` instead.
> In Python, ints are unbounded so it doesn't matter.

## 5. Common pitfalls

- **Off-by-one.** `lo < hi` vs `lo <= hi` and `lo + 1` vs `lo - 1` — every
  binary-search problem gets the off-by-one wrong at least once.
- **Infinite loop.** Make sure your branch always moves `lo` or `hi`. The
  most common cause is `lo = mid` when `lo == hi` to start.
- **Wrong inequality direction.** "First `True`" vs "last `True`" depends
  on the predicate's shape.
- **Sentinel values.** Using `int_min`/`int_max` is convenient but can
  produce nonsense if the true values can be near the sentinel. Use
  `Optional<Integer>` in Java, or floats in Python.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then the [problems/](./problems/) in order.

## Key terms

binary search · monotone predicate · `lo + (hi - lo) // 2` ·
search on answer · partition · sentinel

**Next →** [Module 06: Linked List](../06-linked-list/)
