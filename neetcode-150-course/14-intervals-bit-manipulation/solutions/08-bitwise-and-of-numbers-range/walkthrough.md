# Bitwise AND of Numbers Range - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

Given two integers `left` and `right` that represent the range `[left, right]`, return the bitwise AND of all numbers in this range, inclusive.

## Examples

- `left = 5, right = 7` &rarr; `4`
- `left = 0, right = 0` &rarr; `0`
- `left = 1, right = 2147483647` &rarr; `0`

## Constraints

- 0 <= left <= right <= 2^31 - 1

## Intuition

The AND of all numbers in `[left, right]` is the common bit
prefix. Shift both right until equal, then shift back.

Note: in Java, use `>>>` (unsigned right shift) to avoid sign
extension on the top bit.

**Time:** O(log max). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
