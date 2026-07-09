# Bitwise AND of Numbers Range

**Difficulty:** Medium

## Problem

Given two integers `left` and `right` that represent the range `[left, right]`, return the bitwise AND of all numbers in this range, inclusive.

## Examples

```
Input:  left = 5, right = 7
Output: 4
```

```
Input:  left = 0, right = 0
Output: 0
```

```
Input:  left = 1, right = 2147483647
Output: 0
```

## Constraints

- 0 <= left <= right <= 2^31 - 1

## Hints

1. The result is the common prefix of left and right in binary.
2. Shift both right until equal, count the shifts, shift back.

## Solution

See [`../../solutions/08-bitwise-and-of-numbers-range/`](../../solutions/08-bitwise-and-of-numbers-range/) for the Python and Java 21 solutions and a step-by-step walkthrough.
