# Reverse Linked List - walkthrough

**Difficulty:** Easy &middot; **Module:** 06 Linked List

## Brief

Given the `head` of a singly linked list, reverse the list, and return the reversed list.

## Examples

- `head = [1,2,3,4,5]` &rarr; `[5,4,3,2,1]`
- `head = [1,2]` &rarr; `[2,1]`
- `head = []` &rarr; `[]`

## Constraints

- 0 <= number of nodes <= 5000
- -5000 <= Node.val <= 5000

## Intuition

Iterative three-pointer reverse. We keep `prev` (the new tail so far)
and walk through, reversing each link. The new head is the last `prev`.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
