# Best Time to Buy and Sell Stock IV - walkthrough

**Difficulty:** Hard &middot; **Module:** 12 Dynamic Programming

## Brief

You are given an integer array `prices` where `prices[i]` is the price of a given stock on the ith day, and an integer `k`. Find the maximum profit you can achieve. You may complete at most `k` transactions.

## Examples

- `k = 2, prices = [2,4,1]` &rarr; `2`
- `k = 2, prices = [3,2,6,5,0,3]` &rarr; `7`

## Constraints

- 0 <= k <= 100
- 0 <= len(prices) <= 1000
- 0 <= prices[i] <= 1000

## Intuition

Two arrays of size k+1: `buy[j]` and `sell[j]`. For each price,
update all `j`. If `k >= n / 2`, the unlimited answer applies.

**Time:** O(n · k). **Space:** O(k).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
