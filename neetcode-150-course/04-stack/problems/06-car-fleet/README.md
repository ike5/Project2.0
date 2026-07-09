# Car Fleet

**Difficulty:** Medium

## Problem

There are `n` cars going to the same destination along a one-lane road. The destination is `target` miles away. You are given two integer arrays `position` and `speed`, both of length `n`, where `position[i]` is the position of the ith car and `speed[i]` is its speed. A car can never pass another car ahead of it, but it can catch up to it and drive bumper-to-bumper at the same speed. A car fleet is a non-empty set of cars driving at the same speed with no cars ahead of them. Return the number of car fleets.

## Examples

```
Input:  target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]
Output: 3
```

```
Input:  target = 10, position = [3], speed = [3]
Output: 1
```

## Constraints

- n == position.length == speed.length
- 1 <= n <= 10^5
- 0 < target <= 10^6
- 0 <= position[i] < target
- 0 < speed[i] < 10^6

## Hints

1. Sort cars by position descending (closest to target first).
2. For each car, compute the time it would take alone. Stack of times; if the time is <= the fleet in front, it joins that fleet.

## Solution

See [`../../solutions/06-car-fleet/`](../../solutions/06-car-fleet/) for the Python and Java 21 solutions and a step-by-step walkthrough.
