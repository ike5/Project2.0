# Min Stack - walkthrough

**Difficulty:** Medium &middot; **Module:** 04 Stack

## Brief

Design a stack that supports push, pop, top, and retrieving the minimum element in constant time. Implement the `MinStack` class with `push(x)`, `pop()`, `top()`, and `get_min()` methods.

## Examples

- `MinStack(); push(-2); push(0); push(-3); get_min() -> -3; pop(); top() -> 0; get_min() -> -2` &rarr; `[-3, 0, -2]`

## Constraints

- -2^31 <= x <= 2^31 - 1
- Methods must run in O(1) time
- Up to 3 * 10^4 calls

## Intuition

Two natural approaches:

- **Two stacks** (values, running mins).
- **One stack of (value, min-so-far) pairs** (the Java version above).

Both give O(1) per operation. The pair version is slightly more compact.

**Time:** O(1) per op. **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
