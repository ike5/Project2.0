# Linked List Cycle - walkthrough

**Difficulty:** Easy &middot; **Module:** 06 Linked List

## Brief

Given `head`, the head of a linked list, determine if the linked list has a cycle in it. Return `True` if there is a cycle, `False` otherwise.

## Examples

- `head = [3,2,0,-4], pos = 1 (cycle back to index 1)` &rarr; `True`
- `head = [1,2], pos = -1 (no cycle)` &rarr; `False`

## Constraints

- 0 <= number of nodes <= 10^4
- -10^5 <= Node.val <= 10^5
- pos is -1 or a valid index

## Intuition

Floyd's tortoise and hare. If the list has a cycle, the fast
pointer will eventually lap the slow one and they'll be at the same
node.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
