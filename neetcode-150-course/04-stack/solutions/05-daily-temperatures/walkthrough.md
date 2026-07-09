# Daily Temperatures - walkthrough

**Difficulty:** Medium &middot; **Module:** 04 Stack

## Brief

Given an array of integers `temperatures` representing daily temperatures, return an array `answer` such that `answer[i]` is the number of days you have to wait after the ith day to get a warmer temperature. If there is no future day with a warmer temperature, set `answer[i] = 0`.

## Examples

- `temperatures = [73,74,75,71,69,72,76,73]` &rarr; `[1,1,4,2,1,1,0,0]`
- `temperatures = [30,40,50,60]` &rarr; `[1,1,1,0]`

## Constraints

- 1 <= len(temperatures) <= 10^5
- 30 <= temperatures[i] <= 100

## Intuition

Monotonic stack of indices with *strictly decreasing* temperatures.
For each new day, pop everything cooler and record the answer.

**Time:** O(n) — each index is pushed and popped at most once.
**Space:** O(n) in the worst case (monotonically decreasing input).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
