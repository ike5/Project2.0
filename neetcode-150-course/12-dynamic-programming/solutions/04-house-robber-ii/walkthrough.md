# House Robber II - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Same problem as House Robber, but the houses are arranged in a **circle**. That means the first and last houses are adjacent.

## Examples

- `nums = [2,3,2]` &rarr; `3`
- `nums = [1,2,3,1]` &rarr; `4`
- `nums = [0]` &rarr; `0`

## Constraints

- 1 <= nums.length <= 100
- 0 <= nums[i] <= 1000

## Intuition

Two cases: skip the first, or skip the last. Run House Robber on
each subrange.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
