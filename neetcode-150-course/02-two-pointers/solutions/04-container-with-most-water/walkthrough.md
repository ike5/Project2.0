# Container With Most Water - walkthrough

**Difficulty:** Medium &middot; **Module:** 02 Two Pointers

## Brief

Given `n` non-negative integers `height` where each represents a point at coordinate `(i, height[i])`, find two lines that together with the x-axis form a container that holds the most water.

## Examples

- `height = [1,8,6,2,5,4,8,3,7]` &rarr; `49`
- `height = [1,1]` &rarr; `1`

## Constraints

- 2 <= n <= 10^5
- 0 <= height[i] <= 10^4

## Intuition

Greedy two pointers. Start widest; move the shorter side inward (moving
the taller one cannot increase the area at any later step).

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
