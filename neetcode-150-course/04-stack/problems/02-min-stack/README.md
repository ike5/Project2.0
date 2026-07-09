# Min Stack

**Difficulty:** Medium

## Problem

Design a stack that supports push, pop, top, and retrieving the minimum element in constant time. Implement the `MinStack` class with `push(x)`, `pop()`, `top()`, and `get_min()` methods.

## Examples

```
Input:  MinStack(); push(-2); push(0); push(-3); get_min() -> -3; pop(); top() -> 0; get_min() -> -2
Output: [-3, 0, -2]
```

## Constraints

- -2^31 <= x <= 2^31 - 1
- Methods must run in O(1) time
- Up to 3 * 10^4 calls

## Hints

1. Two-stack approach: one for values, one for the running min.
2. Single-stack approach: store (value, min-so-far) tuples.

## Solution

See [`../../solutions/02-min-stack/`](../../solutions/02-min-stack/) for the Python and Java 21 solutions and a step-by-step walkthrough.
