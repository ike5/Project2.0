# Best Time to Buy and Sell Stock III

**Difficulty:** Hard

## Problem

You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day. Find the maximum profit you can achieve. You may complete **at most two transactions**. Note: You may not engage in multiple transactions simultaneously (i.e., you must sell the stock before you buy again).

## Examples

```
Input:  prices = [3,3,5,0,0,3,1,4]
Output: 6
```

```
Input:  prices = [1,2,3,4,5]
Output: 4
```

## Constraints

- 1 <= len(prices) <= 10^5
- 0 <= prices[i] <= 10^5

## Hints

1. DP with four states: buy1, sell1, buy2, sell2.

## Solution

See [`../../solutions/20-best-time-to-buy-and-sell-stock-iii/`](../../solutions/20-best-time-to-buy-and-sell-stock-iii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
