# Container With Most Water

**Difficulty:** Medium

## Problem

Given `n` non-negative integers `height` where each represents a point at coordinate `(i, height[i])`, find two lines that together with the x-axis form a container that holds the most water.

## Examples

```
Input:  height = [1,8,6,2,5,4,8,3,7]
Output: 49
```

```
Input:  height = [1,1]
Output: 1
```

## Constraints

- 2 <= n <= 10^5
- 0 <= height[i] <= 10^4

## Hints

1. Brute force tries every pair: O(n²). Two pointers does it in O(n).
2. Start with the widest container; only move the *shorter* line in, because moving the taller one can never increase the area.

## Solution

See [`../../solutions/04-container-with-most-water/`](../../solutions/04-container-with-most-water/) for the Python and Java 21 solutions and a step-by-step walkthrough.
