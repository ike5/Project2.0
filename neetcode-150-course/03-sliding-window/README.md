# Module 03 — Sliding Window 🪟

**Goal:** turn a "longest/shortest subarray" problem into a single O(n)
linear pass. ⏱️ ~4 h · 🎯 Prereq: 02.

```
sliding window: an inner loop that wants to be amortized O(1)
```

---

## 1. What is a sliding window?

A **window** is a contiguous range `[l, r]` of an array or string. We
*slide* it across the input by advancing `l` and `r`, maintaining some
property of the window (sum, count, no-repeat, max, ...). The key
optimization: each element enters and leaves the window at most once, so
the total work is O(n) even though the window may visit O(n²) pairs.

## 2. Fixed vs variable windows

| Type | When | Examples |
|------|------|----------|
| **Fixed** | Window size is given | Permutation in String, Sliding Window Maximum, Best Time to Buy (one-element window) |
| **Variable** | Window size is what we're solving for | Longest Substring Without Repeating, Min Size Subarray Sum, Longest Repeating Character Replacement |

The variable-size template:

```python
l = 0
for r in range(n):
    # add nums[r] to window state
    while invalid():
        # remove nums[l] from window state
        l += 1
    # update answer using the current window
```

## 3. The 6 problems — easy → hard

| #  | Problem | Difficulty | Type |
|----|---------|-----------|------|
| 01 | [Best Time to Buy and Sell Stock](./problems/01-best-time-to-buy-and-sell-stock/) | Easy | one-element window |
| 02 | [Longest Substring Without Repeating Characters](./problems/02-longest-substring-without-repeating-characters/) | Medium | variable, with `set` |
| 03 | [Longest Repeating Character Replacement](./problems/03-longest-repeating-character-replacement/) | Medium | variable, with `Counter` |
| 04 | [Permutation in String](./problems/04-permutation-in-string/) | Medium | fixed, compare counts |
| 05 | [Minimum Size Subarray Sum](./problems/05-minimum-size-subarray-sum/) | Medium | variable, sum threshold |
| 06 | [Sliding Window Maximum](./problems/06-sliding-window-maximum/) | Hard | fixed, monotonic deque |

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Deque | `collections.deque` | `ArrayDeque<Integer>` |
| Push left | `dq.appendleft(x)` | `dq.offerFirst(x)` |
| Pop left | `dq.popleft()` | `dq.pollFirst()` |
| Push right | `dq.append(x)` | `dq.offerLast(x)` |
| Pop right | `dq.pop()` | `dq.pollLast()` |
| Peek left | `dq[0]` | `dq.peekFirst()` |
| Peek right | `dq[-1]` | `dq.peekLast()` |
| Counter | `collections.Counter` | `Map<K,Integer>` (manual) |
| Fill array | `[0] * 26` | `new int[26]` |
| Compare arrays | `a == b` | `Arrays.equals(a, b)` |
| Sort a string's chars | `sorted(s)` | `char[] ch = s.toCharArray(); Arrays.sort(ch); new String(ch)` |

## 5. Common pitfalls

- **Wrong window state.** Decide *exactly* what you need to track in the
  window (sum, count, set of indices) and update it on every push/pop.
- **Stale `max_count`.** In *Longest Repeating Character Replacement*,
  the max count only goes up; never decrease it. Decreasing on shrink is
  the #1 bug.
- **Off-by-one.** Sliding windows are inclusive on both sides, so length
  is `r - l + 1`, not `r - l`.
- **Empty input.** Some problems allow `len == 0`; make sure the loop
  doesn't crash.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then the [problems/](./problems/) in order.

## Key terms

sliding window · fixed-size · variable-size · window state · amortized O(1) ·
monotonic deque · shrink-from-the-left

**Next →** [Module 04: Stack](../04-stack/)
