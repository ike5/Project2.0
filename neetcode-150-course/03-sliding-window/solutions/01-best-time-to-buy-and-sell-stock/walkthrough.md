# Best Time to Buy and Sell Stock - walkthrough

**Difficulty:** Easy &middot; **Module:** 03 Sliding Window

## Brief

You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day. You want to maximize your profit by choosing a single day to buy and a different day in the future to sell. Return the maximum profit. If no profit is possible, return 0.

## Examples

- `prices = [7,1,5,3,6,4]` &rarr; `5`
- `prices = [7,6,4,3,1]` &rarr; `0`

## Constraints

- 1 <= len(prices) <= 10^5
- 0 <= prices[i] <= 10^4

## Intuition

Track the minimum price seen so far. The maximum profit ending at day
`i` is `prices[i] - min(prices[0..i])`. One pass, O(n) time, O(1) space.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
