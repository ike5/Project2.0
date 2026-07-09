# Gas Station - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

There are `n` gas stations along a circular route. You have a car with an unlimited gas tank. You are given two integer arrays `gas` and `cost` of length `n`. `gas[i]` is the amount of gas at the ith station, and `cost[i]` is the amount of gas needed to travel from the ith station to the (i + 1)th. You start with an empty tank at one of the gas stations. Return the starting gas station's index if you can travel around the circuit once, otherwise return -1.

## Examples

- `gas = [1,2,3,4,5], cost = [3,4,5,1,2]` &rarr; `3`
- `gas = [2,3,4], cost = [3,4,3]` &rarr; `-1`

## Constraints

- 1 <= gas.length == cost.length <= 10^5
- 0 <= gas[i], cost[i] <= 10^4

## Intuition

Greedy. If we can't make it from `i` to `i+1`, no station in
`[start, i]` can be a valid start; reset `start` to `i+1`.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
