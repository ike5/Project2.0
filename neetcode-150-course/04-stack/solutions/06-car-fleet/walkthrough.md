# Car Fleet - walkthrough

**Difficulty:** Medium &middot; **Module:** 04 Stack

## Brief

There are `n` cars going to the same destination along a one-lane road. The destination is `target` miles away. You are given two integer arrays `position` and `speed`, both of length `n`, where `position[i]` is the position of the ith car and `speed[i]` is its speed. A car can never pass another car ahead of it, but it can catch up to it and drive bumper-to-bumper at the same speed. A car fleet is a non-empty set of cars driving at the same speed with no cars ahead of them. Return the number of car fleets.

## Examples

- `target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]` &rarr; `3`
- `target = 10, position = [3], speed = [3]` &rarr; `1`

## Constraints

- n == position.length == speed.length
- 1 <= n <= 10^5
- 0 < target <= 10^6
- 0 <= position[i] < target
- 0 < speed[i] < 10^6

## Intuition

Sort cars by position descending. Compute each car's *time to target
alone*. A car joins the fleet in front if its time is `<=` the front car's
time. Otherwise, it starts a new fleet.

**Time:** O(n log n) for the sort. **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
