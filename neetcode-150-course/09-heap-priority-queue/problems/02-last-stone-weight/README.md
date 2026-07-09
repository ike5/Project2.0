# Last Stone Weight

**Difficulty:** Easy

## Problem

You are given an array of integers `stones` where `stones[i]` is the weight of the ith stone. Each turn, we choose the two heaviest stones and smash them together. If the stones are equal, both are destroyed. Otherwise, the lighter stone is destroyed and the heavier stone has its weight reduced by the lighter's. Return the smallest possible weight of the last stone (or 0 if no stones remain).

## Examples

```
Input:  stones = [2,7,4,1,8,1]
Output: 1
```

```
Input:  stones = [1]
Output: 1
```

## Constraints

- 1 <= len(stones) <= 30
- 1 <= stones[i] <= 1000

## Hints

1. A max-heap. Pop two, push the difference (or nothing if equal).

## Solution

See [`../../solutions/02-last-stone-weight/`](../../solutions/02-last-stone-weight/) for the Python and Java 21 solutions and a step-by-step walkthrough.
