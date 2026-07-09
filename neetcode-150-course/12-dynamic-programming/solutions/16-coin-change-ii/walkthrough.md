# Coin Change II - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given an array of **distinct** integers `coins` and an integer `amount`, return the number of combinations that make up that amount. You may use each coin unlimited times. The order of coins doesn't matter.

## Examples

- `amount = 5, coins = [1,2,5]` &rarr; `4`
- `amount = 3, coins = [2]` &rarr; `0`
- `amount = 10, coins = [10]` &rarr; `1`

## Constraints

- 1 <= coins.length <= 300
- 1 <= coins[i] <= 5000
- All coins are unique
- 0 <= amount <= 5000

## Intuition

Outer loop over coins. Each combination is built up in a
canonical order (smallest coin first), so we don't double-count.

**Time:** O(n · amount). **Space:** O(amount).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
