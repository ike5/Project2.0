# Koko Eating Bananas

**Difficulty:** Medium

## Problem

Koko loves to eat bananas. There are `n` piles of bananas, the ith pile has `piles[i]` bananas. The guards have gone and will come back in `h` hours. Koko can decide her bananas-per-hour eating speed of `k`. Each hour, she chooses some pile of bananas and eats `k` bananas from that pile. If the pile has less than `k` bananas, she eats all of them and won't eat any more bananas during that hour. Return the minimum integer `k` such that she can eat all the bananas within `h` hours.

## Examples

```
Input:  piles = [1,4,3,2], h = 9
Output: 2
```

```
Input:  piles = [25,10,23,4], h = 4
Output: 25
```

## Constraints

- 1 <= piles.length <= 10^4
- piles.length <= h <= 10^9
- 1 <= piles[i] <= 10^9

## Hints

1. Binary search on the answer (k).
2. If a candidate k is too slow, increase. If fast enough, try smaller.

## Solution

See [`../../solutions/03-koko-eating-bananas/`](../../solutions/03-koko-eating-bananas/) for the Python and Java 21 solutions and a step-by-step walkthrough.
