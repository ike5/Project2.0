# Merge Triplets to Form Target Triplet - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

A **triplet** is an array of three integers. You are given a 2D integer array `triplets`, where `triplets[i] = [ai, bi, ci]` describes the ith triplet. You are also given an integer array `target = [x, y, z]` that describes the triplet you want to obtain. Return `True` if it is possible to obtain the `target` triplet as an element of `triplets`, or `False` otherwise.

## Examples

- `triplets = [[2,5,3],[1,8,4],[1,7,5]], target = [2,7,5]` &rarr; `True`
- `triplets = [[3,4,5],[4,5,6]], target = [3,2,5]` &rarr; `False`
- `triplets = [[2,5,3],[2,5,4],[2,5,5]], target = [2,5,5]` &rarr; `True`

## Constraints

- 1 <= triplets.length <= 10^5
- triplets[i].length == 3
- 0 <= ai, bi, ci <= 1000
- 0 <= x, y, z <= 1000

## Intuition

A triplet can be merged only if each coordinate is `<= target`.
Take the max of all mergeable triplets per coordinate. If the result
equals target, return True.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
