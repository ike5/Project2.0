# Best Time to Buy and Sell Stock

**Difficulty:** Easy

## Problem

You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day. You want to maximize your profit by choosing a single day to buy and a different day in the future to sell. Return the maximum profit. If no profit is possible, return 0.

## Examples

```
Input:  prices = [7,1,5,3,6,4]
Output: 5
```

```
Input:  prices = [7,6,4,3,1]
Output: 0
```

## Constraints

- 1 <= len(prices) <= 10^5
- 0 <= prices[i] <= 10^4

## Hints

1. Track the minimum price seen so far.
2. At each price, the best sell-today profit is `prices[i] - min_so_far`.

## Solution

See [`../../solutions/01-best-time-to-buy-and-sell-stock/`](../../solutions/01-best-time-to-buy-and-sell-stock/) for the Python and Java 21 solutions and a step-by-step walkthrough.
