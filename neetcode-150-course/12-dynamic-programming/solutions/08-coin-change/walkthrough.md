# Coin Change - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given an array `coins` representing coin denominations and an integer `amount`, return the fewest number of coins needed to make up that amount. Return -1 if it's impossible.

## Examples

- `coins = [1,5,10,25], amount = 30` &rarr; `2`
- `coins = [2], amount = 3` &rarr; `-1`

## Constraints

- 1 <= coins.length <= 12
- 1 <= coins[i] <= 2^31 - 1
- 0 <= amount <= 10^4

## Intuition

Bottom-up DP. `dp[a]` = min coins to make `a`. We try each coin
and update.

**Time:** O(n · amount). **Space:** O(amount).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
