# Sliding Window Maximum - walkthrough

**Difficulty:** Hard &middot; **Module:** 03 Sliding Window

## Brief

You are given an array of integers `nums`, and an integer `k`. There is a sliding window of size `k` which moves from the very left of the array to the very right. Return the max of each window.

## Examples

- `nums = [1,3,-1,-3,5,3,6,7], k = 3` &rarr; `[3,3,5,5,6,7]`
- `nums = [1], k = 1` &rarr; `[1]`

## Constraints

- 1 <= len(nums) <= 10^5
- -10^4 <= nums[i] <= 10^4
- 1 <= k <= len(nums)

## Intuition

A **monotonic deque** stores indices in decreasing-value order. The
front is always the max of the current window. On each new element:

1. Pop from the back while the back's value is `<=` the new value (those
   indices can never be a max while the new one is in the window).
2. Push the new index.
3. If the front's index fell out of the window, pop it.
4. Once the first full window is in, record `nums[front]`.

**Time:** O(n) — each index is pushed and popped at most once.
**Space:** O(k).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
