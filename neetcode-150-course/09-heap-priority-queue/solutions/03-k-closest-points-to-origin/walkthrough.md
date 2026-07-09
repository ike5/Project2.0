# K Closest Points to Origin - walkthrough

**Difficulty:** Medium &middot; **Module:** 09 Heap Priority Queue

## Brief

Given an array of `points` where `points[i] = [xi, yi]` represents a point on the X-Y plane and an integer `k`, return the `k` closest points to the origin (0, 0). The distance is the Euclidean distance (`sqrt(x^2 + y^2)`). You may return the answer in any order.

## Examples

- `points = [[1,3],[-2,2]], k = 2` &rarr; `[[-2,2],[1,3]]`
- `points = [[3,3],[5,-1],[-2,4]], k = 2` &rarr; `[[3,3],[-2,4]]`

## Constraints

- 1 <= k <= len(points) <= 10^4
- -10^4 <= xi, yi <= 10^4

## Intuition

Max-heap of size k keyed on squared distance. The `sqrt` cancels
out (it's monotone), so we can compare squared distances.

**Time:** O(n log k). **Space:** O(k).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
