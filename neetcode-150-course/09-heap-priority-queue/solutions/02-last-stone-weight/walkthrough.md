# Last Stone Weight - walkthrough

**Difficulty:** Easy &middot; **Module:** 09 Heap Priority Queue

## Brief

You are given an array of integers `stones` where `stones[i]` is the weight of the ith stone. Each turn, we choose the two heaviest stones and smash them together. If the stones are equal, both are destroyed. Otherwise, the lighter stone is destroyed and the heavier stone has its weight reduced by the lighter's. Return the smallest possible weight of the last stone (or 0 if no stones remain).

## Examples

- `stones = [2,7,4,1,8,1]` &rarr; `1`
- `stones = [1]` &rarr; `1`

## Constraints

- 1 <= len(stones) <= 30
- 1 <= stones[i] <= 1000

## Intuition

A max-heap. Pop two heaviest, push the difference if any. Repeat
until at most one remains.

**Time:** O(n log n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
