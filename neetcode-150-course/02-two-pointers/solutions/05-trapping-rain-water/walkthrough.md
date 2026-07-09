# Trapping Rain Water - walkthrough

**Difficulty:** Hard &middot; **Module:** 02 Two Pointers

## Brief

Given `n` non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.

## Examples

- `height = [0,1,0,2,1,0,1,3,2,1,2,1]` &rarr; `6`
- `height = [4,2,0,3,2,5]` &rarr; `9`

## Constraints

- n == len(height)
- 1 <= n <= 2 * 10^4
- 0 <= height[i] <= 10^5

## Intuition

Water at index i is `min(max_left, max_right) - height[i]`. We don't
need to precompute the max arrays: a two-pointer pass with `lMax` and `rMax`
does the same job in O(1) extra space.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
