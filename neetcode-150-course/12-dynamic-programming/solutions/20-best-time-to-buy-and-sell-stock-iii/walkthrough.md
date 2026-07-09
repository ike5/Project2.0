# Best Time to Buy and Sell Stock III - walkthrough

**Difficulty:** Hard &middot; **Module:** 12 Dynamic Programming

## Brief

You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day. Find the maximum profit you can achieve. You may complete **at most two transactions**. Note: You may not engage in multiple transactions simultaneously (i.e., you must sell the stock before you buy again).

## Examples

- `prices = [3,3,5,0,0,3,1,4]` &rarr; `6`
- `prices = [1,2,3,4,5]` &rarr; `4`

## Constraints

- 1 <= len(prices) <= 10^5
- 0 <= prices[i] <= 10^5

## Intuition

Four states. `buy1`: best profit after first buy; `sell1`: best
profit after first sell; `buy2`: best after second buy; `sell2`: best
after second sell.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
