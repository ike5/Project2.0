# Merge Triplets to Form Target Triplet

**Difficulty:** Medium

## Problem

A **triplet** is an array of three integers. You are given a 2D integer array `triplets`, where `triplets[i] = [ai, bi, ci]` describes the ith triplet. You are also given an integer array `target = [x, y, z]` that describes the triplet you want to obtain. Return `True` if it is possible to obtain the `target` triplet as an element of `triplets`, or `False` otherwise.

## Examples

```
Input:  triplets = [[2,5,3],[1,8,4],[1,7,5]], target = [2,7,5]
Output: True
```

```
Input:  triplets = [[3,4,5],[4,5,6]], target = [3,2,5]
Output: False
```

```
Input:  triplets = [[2,5,3],[2,5,4],[2,5,5]], target = [2,5,5]
Output: True
```

## Constraints

- 1 <= triplets.length <= 10^5
- triplets[i].length == 3
- 0 <= ai, bi, ci <= 1000
- 0 <= x, y, z <= 1000

## Hints

1. A triplet can contribute to the target iff each of its coordinates is <= the target's coordinate. AND the result exactly equals the target.

## Solution

See [`../../solutions/06-merge-triplets-to-form-target/`](../../solutions/06-merge-triplets-to-form-target/) for the Python and Java 21 solutions and a step-by-step walkthrough.
