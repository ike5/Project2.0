# Copy List With Random Pointer - walkthrough

**Difficulty:** Medium &middot; **Module:** 06 Linked List

## Brief

Construct a deep copy of a linked list where each node has an additional `random` pointer that could point to any node in the list or null. Return the head of the deep copy.

## Examples

- `head = [[7,null],[13,0],[11,4],[10,2],[1,0]]` &rarr; `[[7,null],[13,0],[11,4],[10,2],[1,0]]`

## Constraints

- 0 <= n <= 1000
- -10^4 <= Node.val <= 10^4

## Intuition

**Interleave trick** — three passes:

1. Insert a clone right after each original (A → A' → B → B' → ...).
2. For each original, set `clone.random = original.random.next`.
3. Split into two lists.

**Time:** O(n). **Space:** O(1) extra (besides the new nodes).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
