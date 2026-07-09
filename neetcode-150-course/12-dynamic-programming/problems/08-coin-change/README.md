# Coin Change

**Difficulty:** Medium

## Problem

Given an array `coins` representing coin denominations and an integer `amount`, return the fewest number of coins needed to make up that amount. Return -1 if it's impossible.

## Examples

```
Input:  coins = [1,5,10,25], amount = 30
Output: 2
```

```
Input:  coins = [2], amount = 3
Output: -1
```

## Constraints

- 1 <= coins.length <= 12
- 1 <= coins[i] <= 2^31 - 1
- 0 <= amount <= 10^4

## Hints

1. `dp[a] = min(dp[a], dp[a - c] + 1) for c in coins`.

## Solution

See [`../../solutions/08-coin-change/`](../../solutions/08-coin-change/) for the Python and Java 21 solutions and a step-by-step walkthrough.
