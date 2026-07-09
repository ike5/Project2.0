# K Closest Points to Origin

**Difficulty:** Medium

## Problem

Given an array of `points` where `points[i] = [xi, yi]` represents a point on the X-Y plane and an integer `k`, return the `k` closest points to the origin (0, 0). The distance is the Euclidean distance (`sqrt(x^2 + y^2)`). You may return the answer in any order.

## Examples

```
Input:  points = [[1,3],[-2,2]], k = 2
Output: [[-2,2],[1,3]]
```

```
Input:  points = [[3,3],[5,-1],[-2,4]], k = 2
Output: [[3,3],[-2,4]]
```

## Constraints

- 1 <= k <= len(points) <= 10^4
- -10^4 <= xi, yi <= 10^4

## Hints

1. Use a max-heap of size k keyed on squared distance.
2. Or quickselect (O(n) average, O(n^2) worst).

## Solution

See [`../../solutions/03-k-closest-points-to-origin/`](../../solutions/03-k-closest-points-to-origin/) for the Python and Java 21 solutions and a step-by-step walkthrough.
