# Trapping Rain Water

**Difficulty:** Hard

## Problem

Given `n` non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.

## Examples

```
Input:  height = [0,1,0,2,1,0,1,3,2,1,2,1]
Output: 6
```

```
Input:  height = [4,2,0,3,2,5]
Output: 9
```

## Constraints

- n == len(height)
- 1 <= n <= 2 * 10^4
- 0 <= height[i] <= 10^5

## Hints

1. Water at index i = min(max_left, max_right) - height[i].
2. Two-pointer version: keep `l_max` and `r_max`, advance the side with the smaller running max.
3. Alternative: a stack of decreasing heights (Module 04).

## Solution

See [`../../solutions/05-trapping-rain-water/`](../../solutions/05-trapping-rain-water/) for the Python and Java 21 solutions and a step-by-step walkthrough.
