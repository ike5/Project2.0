# Koko Eating Bananas - walkthrough

**Difficulty:** Medium &middot; **Module:** 05 Binary Search

## Brief

Koko loves to eat bananas. There are `n` piles of bananas, the ith pile has `piles[i]` bananas. The guards have gone and will come back in `h` hours. Koko can decide her bananas-per-hour eating speed of `k`. Each hour, she chooses some pile of bananas and eats `k` bananas from that pile. If the pile has less than `k` bananas, she eats all of them and won't eat any more bananas during that hour. Return the minimum integer `k` such that she can eat all the bananas within `h` hours.

## Examples

- `piles = [1,4,3,2], h = 9` &rarr; `2`
- `piles = [25,10,23,4], h = 4` &rarr; `25`

## Constraints

- 1 <= piles.length <= 10^4
- piles.length <= h <= 10^9
- 1 <= piles[i] <= 10^9

## Intuition

Binary search on the eating speed. For a candidate `k`, the number
of hours needed is `sum(ceil(p / k) for p in piles)`. The predicate
"can finish in `h` hours" is monotone in `k` (faster → fewer hours), so
we can binary-search.

**Time:** O(n log(max(p))). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
