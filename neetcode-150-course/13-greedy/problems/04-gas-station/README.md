# Gas Station

**Difficulty:** Medium

## Problem

There are `n` gas stations along a circular route. You have a car with an unlimited gas tank. You are given two integer arrays `gas` and `cost` of length `n`. `gas[i]` is the amount of gas at the ith station, and `cost[i]` is the amount of gas needed to travel from the ith station to the (i + 1)th. You start with an empty tank at one of the gas stations. Return the starting gas station's index if you can travel around the circuit once, otherwise return -1.

## Examples

```
Input:  gas = [1,2,3,4,5], cost = [3,4,5,1,2]
Output: 3
```

```
Input:  gas = [2,3,4], cost = [3,4,3]
Output: -1
```

## Constraints

- 1 <= gas.length == cost.length <= 10^5
- 0 <= gas[i], cost[i] <= 10^4

## Hints

1. If total gas >= total cost, a solution exists. The starting index is the first index after which the running tank never dips below 0.

## Solution

See [`../../solutions/04-gas-station/`](../../solutions/04-gas-station/) for the Python and Java 21 solutions and a step-by-step walkthrough.
