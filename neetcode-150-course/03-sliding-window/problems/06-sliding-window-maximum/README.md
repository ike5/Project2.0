# Sliding Window Maximum

**Difficulty:** Hard

## Problem

You are given an array of integers `nums`, and an integer `k`. There is a sliding window of size `k` which moves from the very left of the array to the very right. Return the max of each window.

## Examples

```
Input:  nums = [1,3,-1,-3,5,3,6,7], k = 3
Output: [3,3,5,5,6,7]
```

```
Input:  nums = [1], k = 1
Output: [1]
```

## Constraints

- 1 <= len(nums) <= 10^5
- -10^4 <= nums[i] <= 10^4
- 1 <= k <= len(nums)

## Hints

1. Brute force: max of each window — O(n · k).
2. Faster: a **deque** storing indices of candidates in decreasing value order. The front is always the window max.

## Solution

See [`../../solutions/06-sliding-window-maximum/`](../../solutions/06-sliding-window-maximum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
