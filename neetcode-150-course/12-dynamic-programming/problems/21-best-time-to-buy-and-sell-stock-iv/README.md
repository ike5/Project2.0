# Best Time to Buy and Sell Stock IV

**Difficulty:** Hard

## Problem

You are given an integer array `prices` where `prices[i]` is the price of a given stock on the ith day, and an integer `k`. Find the maximum profit you can achieve. You may complete at most `k` transactions.

## Examples

```
Input:  k = 2, prices = [2,4,1]
Output: 2
```

```
Input:  k = 2, prices = [3,2,6,5,0,3]
Output: 7
```

## Constraints

- 0 <= k <= 100
- 0 <= len(prices) <= 1000
- 0 <= prices[i] <= 1000

## Hints

1. DP with `k` pairs of (buy, sell) states. If `k >= n // 2`, the transactions-unlimited answer applies (just sum the ups).

## Solution

See [`../../solutions/21-best-time-to-buy-and-sell-stock-iv/`](../../solutions/21-best-time-to-buy-and-sell-stock-iv/) for the Python and Java 21 solutions and a step-by-step walkthrough.
