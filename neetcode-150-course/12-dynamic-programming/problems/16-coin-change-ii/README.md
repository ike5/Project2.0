# Coin Change II

**Difficulty:** Medium

## Problem

Given an array of **distinct** integers `coins` and an integer `amount`, return the number of combinations that make up that amount. You may use each coin unlimited times. The order of coins doesn't matter.

## Examples

```
Input:  amount = 5, coins = [1,2,5]
Output: 4
```

```
Input:  amount = 3, coins = [2]
Output: 0
```

```
Input:  amount = 10, coins = [10]
Output: 1
```

## Constraints

- 1 <= coins.length <= 300
- 1 <= coins[i] <= 5000
- All coins are unique
- 0 <= amount <= 5000

## Hints

1. Outer loop on coins, inner loop on amount. This ordering ensures each combination is counted once.

## Solution

See [`../../solutions/16-coin-change-ii/`](../../solutions/16-coin-change-ii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
