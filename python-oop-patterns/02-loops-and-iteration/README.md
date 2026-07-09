# Module 02 — Loops & iteration patterns

**Python skill:** the `for` loop and its companions (`enumerate`, `range`, `while`, two-pointer, sliding window) — the workhorse of every LeetCode problem.
**LeetCode problem:** [121. Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) · Easy.
**Time:** ~1.5 h.

---

## 1. The `for` loop, again

Python's `for` loop is "for each element in an iterable":

```python
for x in xs:
    ...

for i, x in enumerate(xs):
    ...

for a, b in zip(xs, ys):
    ...

for i in range(n):       # 0, 1, ..., n-1
    ...
```

That's basically it. Once you have the right iterable, the body is just business logic.

## 2. `enumerate` beats `range(len(...))`

If you find yourself writing:

```python
for i in range(len(xs)):
    x = xs[i]
    ...
```

Stop. You want:

```python
for i, x in enumerate(xs):
    ...
```

`enumerate` is the same O(1) overhead per step but reads better. The only time you need `range(len(xs))` is when the index is the *point* (e.g. swapping in place).

## 3. `while` for two-pointer and friends

When two indices walk through a sequence (often from both ends, sometimes at different speeds), you want a `while` loop:

```python
left, right = 0, len(nums) - 1
while left < right:
    s = nums[left] + nums[right]
    if s == target:
        return (left, right)
    if s < target:
        left += 1
    else:
        right -= 1
```

This is **two-pointer**: O(n) time, O(1) extra space, works on *sorted* inputs.

## 4. Sliding window

When the problem is "longest/shortest subarray with property X", you usually want a sliding window:

```python
left = 0
window_state = ...              # something O(1) you maintain
for right, x in enumerate(nums):
    add_to_window(window_state, x)
    while violates(window_state):
        remove_from_window(window_state, nums[left])
        left += 1
    answer = max(answer, right - left + 1)
```

The window is `[left, right]` (or `[left, right)`). `right` always moves forward; `left` follows when the window is too big. Total work is O(n) because each index moves forward at most once.

## 5. The LeetCode problem

> [121. Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/)
>
> You are given an array `prices` where `prices[i]` is the price of a stock on day `i`. Choose **one** day to buy and a **later** day to sell to maximize profit. Return `0` if no profit is possible.

There are three solutions that matter:

1. **Brute force (O(n²)):** for every pair `(i, j)` with `j > i`, compute `prices[j] - prices[i]`.
2. **Track the running minimum (O(n)):** as you walk the list, remember the smallest price you've seen. The best profit ending at day `i` is `prices[i] - min_so_far`.
3. **Kadane's on differences (O(n)):** the problem is equivalent to "find the max subarray of `prices[i+1] - prices[i]`".

Solution 2 is the most intuitive. You'll build it in the lab.

## 6. Anti-patterns

- **Re-computing the same thing in a loop.** If you write `min(prices[:i])` inside a loop, that's O(n²). Track `min_so_far` as you go.
- **Calling `len(xs)` in a hot loop.** Python lists don't change length inside a `for`, but if you call `len(xs)` inside the loop body, you're calling a C function for no reason. Hoist it.
- **Looping to build a list, then looping over the list.** Use a comprehension or extend in place.

---

**→ Next: [Module 03 — Classes & `self`](./../03-classes-and-self/)**
