# Best Time to Buy and Sell Stock with Cooldown - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day. Find the maximum profit you can achieve. You may complete as many transactions as you like (i.e., buy one and sell one share of the stock multiple times) with the following **restrictions**: After you sell your stock, you cannot buy stock on the next day (i.e., cooldown one day).

## Examples

- `prices = [1,2,3,0,2]` &rarr; `3`
- `prices = [1]` &rarr; `0`

## Constraints

- 1 <= len(prices) <= 5000
- 0 <= prices[i] <= 1000

## Intuition

Three rolling states. `free` = no stock no cooldown; `hold` =
holding a stock; `sold` = just sold (will become `free` tomorrow).

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
