# Largest Rectangle in Histogram - walkthrough

**Difficulty:** Hard &middot; **Module:** 04 Stack

## Brief

Given an array of integers `heights` representing the histogram's bar height where the width of each bar is 1, return the area of the largest rectangle that can be formed in the histogram.

## Examples

- `heights = [2,1,5,6,2,3]` &rarr; `10`
- `heights = [2,4]` &rarr; `4`

## Constraints

- 1 <= len(heights) <= 10^5
- 0 <= heights[i] <= 10^4

## Intuition

**Monotonic increasing stack** of indices. When we see a bar shorter
than the top, we pop and compute the area using the popped bar's height and
the current index (right boundary) and the new top's index (left boundary).

We append a sentinel `0` at the end so all remaining bars get popped and
accounted for.

**Time:** O(n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
