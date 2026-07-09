# Largest Rectangle in Histogram

**Difficulty:** Hard

## Problem

Given an array of integers `heights` representing the histogram's bar height where the width of each bar is 1, return the area of the largest rectangle that can be formed in the histogram.

## Examples

```
Input:  heights = [2,1,5,6,2,3]
Output: 10
```

```
Input:  heights = [2,4]
Output: 4
```

## Constraints

- 1 <= len(heights) <= 10^5
- 0 <= heights[i] <= 10^4

## Hints

1. Brute force: for each pair (l, r), compute min height and area. O(n²).
2. Monotonic stack: for each bar, find the nearest smaller bar on each side. That's the width of the max rectangle where this bar is the limiting height.

## Solution

See [`../../solutions/07-largest-rectangle-in-histogram/`](../../solutions/07-largest-rectangle-in-histogram/) for the Python and Java 21 solutions and a step-by-step walkthrough.
